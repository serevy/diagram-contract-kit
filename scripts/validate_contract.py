#!/usr/bin/env python3
"""Offline v0.1 contract lint. A pass is never semantic/visual approval."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema/diagram-contract.schema.json"
FACTUAL_INTENTS = {"software_architecture", "dataflow", "state", "policy"}
FACTUAL_DIRECTIVES = {"labelled_entities", "directed_edges", "boundaries"}
PHYSICAL_DIRECTIVES = {"physical_mechanism", "isometric_machine"}


def purpose_hash(contract):
    """Bind the recorded purpose text, not a claim that its meaning was verified."""
    return hashlib.sha256(contract["brief"]["use"].encode("utf-8")).hexdigest()


def load_json(path):
    """Reject duplicate keys and non-JSON constants rather than silently accepting them."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"invalid JSON constant: {value}")

    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=pairs, parse_constant=reject_constant)


def schema_errors(value, schema, root, path="$", errors=None):
    """Implement only the JSON Schema vocabulary used by our bundled schema."""
    if errors is None:
        errors = []
    if "$ref" in schema:
        target = root
        for key in schema["$ref"].removeprefix("#/").split("/"):
            target = target[key]
        return schema_errors(value, target, root, path, errors)
    types = {"object": dict, "array": list, "string": str,
             "boolean": bool, "null": type(None)}
    expected = schema.get("type")
    if expected:
        names = expected if isinstance(expected, list) else [expected]
        if not any(type(value) is types[name] for name in names):
            errors.append(f"SCHEMA {path}: expected {' or '.join(names)}")
            return errors
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        errors.append(f"SCHEMA {path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"SCHEMA {path}: expected one of {schema['enum']}")
    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errors.append(f"SCHEMA {path}: non-blank text required")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"SCHEMA {path}: must match {schema['pattern']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"SCHEMA {path}.{key}: required")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            child = properties.get(key)
            if child is None and additional is False:
                errors.append(f"SCHEMA {path}.{key}: unknown field")
            elif child is not None or isinstance(additional, dict):
                schema_errors(item, child if child is not None else additional,
                              root, f"{path}.{key}", errors)
        if len(value) < schema.get("minProperties", 0):
            errors.append(f"SCHEMA {path}: too few properties")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"SCHEMA {path}: too few items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(x, sort_keys=True, ensure_ascii=False) for x in value]
            if len(set(encoded)) != len(encoded):
                errors.append(f"SCHEMA {path}: duplicate items")
        for i, item in enumerate(value):
            if "items" in schema:
                schema_errors(item, schema["items"], root, f"{path}[{i}]", errors)
    return errors


def local_path(root, value):
    """Accept portable relative paths, contained in the explicit source root."""
    path = PurePosixPath(value)
    if (not value or "\\" in value or ":" in value or path.is_absolute()
            or ".." in path.parts or str(path) != value or value == "."):
        raise ValueError("use a normalized relative POSIX path without '..'")
    try:
        resolved = (root / value).resolve()
    except RuntimeError as exc:
        raise ValueError("path contains a symlink loop") from exc
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("path escapes root (including via symlink)")
    return resolved


def validate(contract, root):
    """Return stable diagnostics; reads sources only, never writes or calls a provider."""
    schema = load_json(SCHEMA_PATH)
    errors = schema_errors(contract, schema, schema)
    if errors:
        return errors  # Never run graph checks against an ill-typed document.

    def fail(code, message):
        errors.append(f"{code}: {message}")

    intent, view = contract["intent"], contract["view"]
    if intent in FACTUAL_INTENTS:
        if view["type"] != "labelled_graph" or view["style"] != "boxes_arrows_boundaries":
            fail("VIEW_MISMATCH", f"{intent} requires labelled boxes/arrows/boundaries; "
                 "remove the physical instrument requirement BEFORE rendering. "
                 "An explicitly requested metaphor belongs in a separate physical_mechanism contract.")
        if view["physical_metaphor_requested"] or contract["brief"]["metaphors"]:
            fail("VIEW_MISMATCH", "factual intent cannot require a physical metaphor; use a separate teaching view")
    elif (view["type"] != "physical_mechanism" or view["style"] != "isometric_machine"
          or not view["physical_metaphor_requested"] or not contract["brief"]["metaphors"]):
        fail("METAPHOR_SELECTION", "physical_mechanism needs explicit user selection and documented metaphors")

    rendering = contract["rendering"]
    expected_directives = FACTUAL_DIRECTIVES if intent in FACTUAL_INTENTS else PHYSICAL_DIRECTIVES
    if set(rendering["directives"]) != expected_directives:
        fail("RENDER_MISMATCH", f"{intent} renderer directives must be {sorted(expected_directives)}; "
             "reconcile the authorized deliverable and rendering instructions BEFORE generation")
    if rendering["purpose_sha256"] != purpose_hash(contract):
        fail("PURPOSE_CHANGED", "brief.use changed since its typed directives were recorded; "
             "reinspect sources and reconcile purpose/instructions before recording a new binding. "
             "Ask a human if meaning remains ambiguous; do not simply rehash contradictory instructions")
    if rendering["ambiguity"] != "clear":
        fail("RENDER_AMBIGUOUS", "purpose or rendering instructions remain unresolved; "
             "clarify against sources or with a human BEFORE generation")

    indexes = {}
    all_ids = set()
    for group in ("sources", "boundaries", "entities", "edges"):
        indexes[group] = {}
        for item in contract[group]:
            identifier = item["id"]
            if identifier in all_ids:
                fail("DUPLICATE_ID", f"{group}.{identifier}: IDs must be globally unique")
            all_ids.add(identifier)
            indexes[group][identifier] = item

    sources = indexes["sources"]
    for scope in ("historical", "current_integration"):
        revision = contract["provenance"][f"{scope}_source_revision" if scope == "historical"
                                          else "current_integration_revision"]
        matching = [s for s in sources.values() if s["scope"] == scope]
        if scope == "historical" and revision is None:
            if matching:
                fail("PROVENANCE", "null historical_source_revision means no historical baseline; "
                     "it cannot coexist with historical source records")
            continue
        if not matching:
            fail("PROVENANCE", f"a {scope} source is required; keep historical evidence separate")
        for source in matching:
            if source["revision"] != revision:
                fail("PROVENANCE", f"{source['id']}: revision disagrees with provenance.{scope}")
    for source in sources.values():
        try:
            path = local_path(root, source["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != source["sha256"]:
                fail("SOURCE_HASH", f"{source['id']}: {source['path']} changed; review current integration "
                     "separately, do not overwrite frozen historical hashes")
        except (OSError, ValueError) as exc:
            fail("SOURCE_PATH", f"{source['id']}: {exc}")

    entities, boundaries, edges = (indexes[k] for k in ("entities", "boundaries", "edges"))
    for group in ("entities", "boundaries", "edges"):
        for item in contract[group]:
            for source_id in item["source_ids"]:
                if source_id not in sources:
                    fail("SOURCE_REF", f"{item['id']}: unknown source {source_id}")
    for boundary in boundaries.values():
        if boundary["kind"] != "deterministic" and boundary["can_authorize"]:
            fail("AUTHORITY", f"{boundary['id']}: only a deterministic boundary may authorize")
    for entity in entities.values():
        boundary = boundaries.get(entity["boundary"])
        if boundary is None:
            fail("BOUNDARY_REF", f"{entity['id']}: unknown boundary {entity['boundary']}")
            continue
        expected = {"classifier": "semantic", "typed_result": "semantic",
                    "policy_gate": "deterministic", "outcome": "deterministic",
                    "rule": "external", "input": "external"}.get(entity["role"])
        if expected is not None and boundary["kind"] != expected:
            fail("AUTHORITY", f"{entity['id']}: {entity['role']} must be in a {expected} boundary")
        if entity["role"] == "policy_gate" and not boundary["can_authorize"]:
            fail("AUTHORITY", f"{entity['id']}: policy gate needs independent deterministic authority")
        if intent in FACTUAL_INTENTS and entity["assertion"] == "metaphorical":
            fail("ASSERTION", f"{entity['id']}: metaphor cannot replace a factual architecture entity")
    for edge in edges.values():
        if edge["from"] not in entities or edge["to"] not in entities:
            fail("EDGE_ENDPOINT", f"{edge['id']}: endpoints must reference existing entities")
        elif edge["kind"] == "control" and (
                entities[edge["from"]]["role"] in {"classifier", "typed_result"} or
                boundaries.get(entities[edge["from"]]["boundary"], {}).get("kind") == "semantic"):
            fail("AUTHORITY", f"{edge['id']}: semantic output is data, never authorization/control")

    models_authorization = any(e["role"] in {"policy_gate", "outcome"} for e in entities.values()) or any(
        b["can_authorize"] for b in boundaries.values())
    if intent in FACTUAL_INTENTS and models_authorization:
        gates = [e for e in entities.values() if e["role"] == "policy_gate"]
        outcomes = [e for e in entities.values() if e["role"] == "outcome"]
        if not gates or not outcomes:
            fail("POLICY_GATE", "authorization flow requires a policy_gate and a protected outcome; "
                 "read-only classification alone does not require either")
        for gate in gates:
            incoming = [edge for edge in edges.values() if edge["to"] == gate["id"]]
            required_inputs = [("rule", "control")]
            if any(e["role"] in {"classifier", "typed_result"} for e in entities.values()):
                required_inputs.append(("typed_result", "data"))
            for role, kind in required_inputs:
                if not any(edge["kind"] == kind and entities.get(edge["from"], {}).get("role") == role
                           and entities.get(edge["from"], {}).get("assertion") == "factual"
                           for edge in incoming):
                    fail("POLICY_GATE", f"{gate['id']}: requires {kind} input from independent {role}")
            if gate["assertion"] != "factual":
                fail("POLICY_GATE", f"{gate['id']}: gate cannot be an unasserted assumption")
        for outcome in outcomes:
            incoming = [edge for edge in edges.values() if edge["to"] == outcome["id"]]
            if not incoming or any(edge["kind"] != "control" or
                                   entities.get(edge["from"], {}).get("role") != "policy_gate"
                                   for edge in incoming):
                fail("POLICY_BYPASS", f"{outcome['id']}: all incoming paths must pass a deterministic policy_gate")

    languages = set(contract["brief"]["languages"])
    if set(contract["locales"]) != languages:
        fail("LOCALE_PARITY", "locale keys must equal brief.languages")
    for locale, labels in contract["locales"].items():
        for group in ("entities", "edges", "boundaries"):
            if set(labels[group]) != set(indexes[group]):
                fail("LOCALE_PARITY", f"{locale}.{group}: label keys must exactly match graph IDs")

    seen_paths = set()
    source_paths = set()
    for source in sources.values():
        try:
            source_paths.add(local_path(root, source["path"]))
        except (OSError, ValueError):
            pass  # Already diagnosed by source checks above.
    for artifact in contract["artifacts"]:
        try:
            output_path = local_path(root, artifact["path"])
            if output_path in source_paths:
                fail("ARTIFACT_PATH", f"output would overwrite source {artifact['path']}")
            if output_path in seen_paths:
                fail("ARTIFACT_PATH", f"duplicate output path {artifact['path']}")
            seen_paths.add(output_path)
        except (OSError, ValueError) as exc:
            fail("ARTIFACT_PATH", f"{artifact['path']}: {exc}")
        if artifact["format"] not in contract["brief"]["acceptable_outputs"]:
            fail("ARTIFACT_FORMAT", f"{artifact['path']}: output is not allowed by brief")
        if artifact["locale"] not in languages:
            fail("ARTIFACT_LOCALE", f"{artifact['path']}: unknown locale {artifact['locale']}")
    if {a["locale"] for a in contract["artifacts"]} != languages:
        fail("ARTIFACT_LOCALE", "declare an artifact for every requested language")

    reviews = contract["review_gates"]
    for name, gate in reviews.items():
        if gate["status"] == "approved" and not (gate["reviewer"] or "").strip():
            fail("REVIEW_GATE", f"{name}: independent human reviewer required for approval")
        if gate["status"] == "pending" and gate["reviewer"] is not None:
            fail("REVIEW_GATE", f"{name}: pending gate must not claim a reviewer")
    if reviews["publication_approval"]["status"] == "approved" and any(
            reviews[name]["status"] != "approved" for name in ("semantic_review", "visual_review")):
        fail("REVIEW_GATE", "publication approval requires separate semantic and visual approvals")
    return errors


def render_plan(contract, root):
    """Validate before deriving typed producer inputs; never forward brief.use as a prompt."""
    errors = validate(contract, root)
    if errors:
        raise ValueError("contract blocked before generation\n" + "\n".join(errors))
    plan = {key: contract[key] for key in
            ("schema_version", "intent", "view", "entities", "edges", "boundaries", "locales", "artifacts")}
    plan["directives"] = sorted(contract["rendering"]["directives"])
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="local source/artifact root (default: current directory)")
    parser.add_argument("--render-plan", action="store_true",
                        help="emit validated typed producer inputs as JSON; never forward free-text purpose instructions")
    args = parser.parse_args(argv)
    try:
        contract = load_json(args.contract)
        errors = validate(contract, args.root)
    except (OSError, ValueError, RecursionError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("FAIL: contract blocked before rendering", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if args.render_plan:
        # ASCII escaping makes JSON output portable even through Windows legacy code pages.
        print(json.dumps(render_plan(contract, args.root), indent=2))
        return 0
    print("PASS: structural contract checks only; semantic/visual review and publication approval remain independent.")
    print("Review gates: " + ", ".join(f"{name}={gate['status']}" for name, gate in contract["review_gates"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
