#!/usr/bin/env python3
"""Reproduce the fixed fictional SVG demo; intentionally not a general renderer."""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from validate_contract import load_json, local_path, render_plan

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "examples/fictional/diagram-contract.json"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

BOXES = {
    "request": (80, 140, 310, 70), "rules": (570, 140, 310, 70),
    "classify": (80, 310, 310, 70), "typed": (80, 460, 310, 70),
    "gate": (570, 460, 310, 70), "hold": (570, 630, 310, 70),
    "review": (570, 780, 310, 70), "eligible": (570, 930, 310, 70),
}
BOUNDARIES = {
    "context": (30, 70, 940, 165), "semantic": (30, 260, 420, 290),
    "deterministic": (510, 260, 460, 770),
}
# path, label x/y: data and independent control are visually distinct.
ROUTES = {
    "request_classify": ("M 235 210 V 245 H 15 V 345 H 80", 140, 252),
    "classify_typed": ("M 235 380 V 460", 235, 422),
    "typed_gate": ("M 390 495 H 570", 480, 480),
    "rules_gate": ("M 725 210 V 245 H 490 V 430 H 725 V 460", 675, 420),
    "gate_hold": ("M 725 530 V 630", 725, 586),
    "gate_review": ("M 880 490 H 915 V 815 H 880", 725, 753),
    "gate_eligible": ("M 880 510 H 945 V 965 H 880", 725, 903),
}


def add(parent, name, attrs=None, text=None):
    node = ET.SubElement(parent, f"{{{NS}}}{name}", attrs or {})
    node.text = text
    return node


def render(contract, locale):
    labels = contract["locales"][locale]
    svg = ET.Element(f"{{{NS}}}svg", {
        "viewBox": "0 0 1000 1100", "width": "1000", "height": "1100",
        "role": "img", "aria-labelledby": "title description", "lang": locale,
    })
    add(svg, "title", {"id": "title"}, labels["title"])
    add(svg, "desc", {"id": "description"}, labels["description"])
    add(svg, "style", text="""
text { font-family: sans-serif; fill: #172438; font-size: 19px; }
.heading { font-weight: bold; font-size: 23px; }
.boundary-label { font-weight: bold; font-size: 20px; }
.edge-label { font-size: 16px; paint-order: stroke; stroke: #fff; stroke-width: 5px; stroke-linejoin: round; }
.box { fill: #fff; stroke: #33465e; stroke-width: 2; }
.data { fill: none; stroke: #245a85; stroke-width: 2; }
.control { fill: none; stroke: #713f12; stroke-width: 3; stroke-dasharray: 7 4; }
""".strip())
    defs = add(svg, "defs")
    for kind, color in (("data", "#245a85"), ("control", "#713f12")):
        marker = add(defs, "marker", {"id": f"arrow-{kind}", "markerWidth": "8",
                     "markerHeight": "8", "refX": "7", "refY": "4", "orient": "auto"})
        add(marker, "path", {"d": "M 0 0 L 8 4 L 0 8 Z", "fill": color})
    add(svg, "rect", {"width": "1000", "height": "1100", "fill": "#fff"})
    add(svg, "text", {"x": "30", "y": "40", "class": "heading"}, labels["title"])
    for boundary in contract["boundaries"]:
        identifier = boundary["id"]
        x, y, w, h = BOUNDARIES[identifier]
        group = add(svg, "g", {"data-boundary-id": identifier})
        color = {"context": "#f1f5f9", "semantic": "#e8f2fc", "deterministic": "#fff5df"}[identifier]
        add(group, "rect", {"x": str(x), "y": str(y), "width": str(w), "height": str(h),
                            "rx": "10", "fill": color, "stroke": "#54657a", "stroke-width": "2"})
        add(group, "text", {"x": str(x+20), "y": str(y+35), "class": "boundary-label"},
            labels["boundaries"][identifier])
    for entity in contract["entities"]:
        identifier = entity["id"]
        x, y, w, h = BOXES[identifier]
        group = add(svg, "g", {"data-entity-id": identifier, "data-boundary": entity["boundary"]})
        add(group, "rect", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "rx": "6", "class": "box"})
        add(group, "text", {"x": str(x+w/2), "y": str(y+h/2+7), "text-anchor": "middle"}, labels["entities"][identifier])
    for edge in contract["edges"]:
        identifier = edge["id"]
        path, x, y = ROUTES[identifier]
        group = add(svg, "g", {"data-edge-id": identifier, "data-from": edge["from"], "data-to": edge["to"]})
        add(group, "path", {"d": path, "class": edge["kind"], "marker-end": f"url(#arrow-{edge['kind']})"})
        add(group, "text", {"x": str(x), "y": str(y), "text-anchor": "middle", "class": "edge-label"}, labels["edges"][identifier])
    footnote = ("Solid: data · Dashed: independent control · Local demo, review pending"
                if locale == "en" else "実線：データ　破線：独立した制御　ローカル例・レビュー待ち")
    add(svg, "text", {"x": "30", "y": "1070"}, footnote)
    ET.indent(svg, space="  ")
    return ET.tostring(svg, encoding="utf-8", xml_declaration=True) + b"\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="require committed SVGs to exist and match; never regenerate")
    args = parser.parse_args(argv)
    contract = load_json(CONTRACT)
    try:
        plan = render_plan(contract, ROOT)
    except ValueError as exc:
        print(f"FAIL: rendering blocked\n{exc}", file=sys.stderr)
        return 1
    # This fixed layout supports only the original demo graph and factual entities.
    expected_roles = {"request": ("input", "context"), "rules": ("rule", "context"),
                      "classify": ("classifier", "semantic"), "typed": ("typed_result", "semantic"),
                      "gate": ("policy_gate", "deterministic"), "hold": ("outcome", "deterministic"),
                      "review": ("outcome", "deterministic"), "eligible": ("outcome", "deterministic")}
    if (plan["view"]["type"] != "labelled_graph"
            or set(plan["directives"]) != {"labelled_entities", "directed_edges", "boundaries"}
            or {e["id"] for e in contract["entities"]} != set(BOXES)
            or {e["id"] for e in contract["edges"]} != set(ROUTES)
            or {b["id"] for b in contract["boundaries"]} != set(BOUNDARIES)
            or any(e["assertion"] != "factual" or (e["role"], e["boundary"]) != expected_roles[e["id"]]
                   for e in contract["entities"])
            or any(e["id"] != f"{e['from']}_{e['to']}" or
                   e["kind"] != ("control" if e["from"] in {"rules", "gate"} else "data")
                   for e in contract["edges"])):
        print("FAIL: fixed demo layout requires the original factual graph; review a new layout", file=sys.stderr)
        return 1
    outputs = []
    for artifact in contract["artifacts"]:
        locale = artifact["locale"]
        if locale not in {"en", "ja"} or artifact["format"] != "svg" or artifact["path"] != f"examples/fictional/architecture.{locale}.svg":
            print("FAIL: demo supports only its declared en/ja SVG paths", file=sys.stderr)
            return 1
        outputs.append((local_path(ROOT, artifact["path"]), render(plan, locale)))
    # Check ALL committed outputs before any regeneration: missing files must fail.
    for path, expected in outputs:
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                print(f"FAIL: missing or stale committed output: {path.relative_to(ROOT.resolve())}", file=sys.stderr)
                return 1
        else:
            path.write_bytes(expected)
    print("PASS: committed SVGs match the demo contract" if args.check else "Wrote local SVG demos; human semantic/visual approval remains pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
