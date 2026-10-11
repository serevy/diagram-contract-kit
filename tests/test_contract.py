"""Deterministic preflight and committed-artifact regression tests (stdlib only)."""

import copy
from contextlib import redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_contract import SCHEMA_PATH, load_json, purpose_hash, render_plan, validate
import render_example

EXAMPLE = ROOT / "examples/fictional/diagram-contract.json"


def symlink_or_skip(test, path, target, **kwargs):
    try:
        path.symlink_to(target, **kwargs)
    except OSError as exc:
        if os.name == 'nt' and getattr(exc, 'winerror', None) in {1, 5, 50, 1314}:
            test.skipTest(f'Windows symlinks unavailable: {exc}')
        raise


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_json(EXAMPLE)

    def assertBlocked(self, code, contract=None, root=ROOT):
        errors = validate(self.contract if contract is None else contract, root)
        self.assertTrue(any(e.startswith(code) for e in errors), errors)

    def test_valid_fictional_contract_and_pending_reviews(self):
        self.assertEqual(validate(self.contract, ROOT), [])
        self.assertTrue(all(g['status'] == 'pending' for g in self.contract['review_gates'].values()))

    def test_spec_bug_physical_tabletop_instrument_before_generation(self):
        """Independently authored reproduction of the #152 → #154 spec error."""
        bad = load_json(ROOT / 'tests/fixtures/bad-physical-instrument.json')
        self.assertEqual(bad['intent'], 'software_architecture')
        self.assertIn('physical tabletop instrument', bad['brief']['use'])
        self.assertBlocked('VIEW_MISMATCH', bad)
        result = subprocess.run([sys.executable, str(ROOT/'scripts/validate_contract.py'),
                                 str(ROOT/'tests/fixtures/bad-physical-instrument.json'), '--root', str(ROOT)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('BEFORE rendering', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_ambiguous_revision_and_assumed_authority_fail(self):
        bad = load_json(ROOT/'tests/fixtures/ambiguous-authority.json')
        self.assertBlocked('PROVENANCE', bad)
        self.assertBlocked('POLICY_GATE', bad)

    def test_all_factual_intents_block_physical_view(self):
        for intent in ('software_architecture', 'dataflow', 'state', 'policy'):
            with self.subTest(intent=intent):
                self.contract['intent'] = intent
                self.contract['view']['type'] = 'physical_mechanism'
                self.assertBlocked('VIEW_MISMATCH')

    def test_explicit_separate_metaphor_allowed_but_not_implicit_selection(self):
        self.contract['intent'] = 'physical_mechanism'
        self.contract['view'] = {'type': 'physical_mechanism', 'style': 'isometric_machine',
                                 'physical_metaphor_requested': True}
        self.contract['brief']['metaphors'] = ['A separately requested physical teaching analogy.']
        self.contract['rendering']['directives'] = ['physical_mechanism', 'isometric_machine']
        self.assertEqual(validate(self.contract, ROOT), [])
        self.contract['view']['physical_metaphor_requested'] = False
        self.assertBlocked('METAPHOR_SELECTION')

    def test_presence_types_unknown_fields_blank_text(self):
        mutations = [lambda c: c.pop('brief'), lambda c: c.update(entities=None),
                     lambda c: c.update(unknown='ignored?'),
                     lambda c: c['brief'].update(audience='  '),
                     lambda c: c['boundaries'][0].update(can_authorize=1),
                     lambda c: c['sources'][0].update(sha256='not-a-hash'),
                     lambda c: c['entities'][0].update(boundary='not valid')]
        for mutate in mutations:
            contract = copy.deepcopy(self.contract)
            mutate(contract)
            self.assertBlocked('SCHEMA', contract)
        self.assertBlocked('SCHEMA', [])

    def test_schema_vocabulary_is_exactly_the_supported_subset(self):
        supported = {'$schema', '$id', 'title', '$defs', '$ref', 'type', 'required',
                     'properties', 'additionalProperties', 'items', 'minItems',
                     'uniqueItems', 'minProperties', 'minLength', 'pattern', 'const', 'enum'}
        def walk(schema):
            self.assertLessEqual(set(schema), supported)
            for key in ('properties', '$defs'):
                for child in schema.get(key, {}).values():
                    walk(child)
            for key in ('items', 'additionalProperties'):
                if isinstance(schema.get(key), dict):
                    walk(schema[key])
            if '$ref' in schema:
                self.assertRegex(schema['$ref'], r'^#/\$defs/[a-z_]+$')
        walk(load_json(SCHEMA_PATH))

    def test_duplicate_ids_and_dangling_references(self):
        self.contract['entities'][1]['id'] = 'request'
        self.assertBlocked('DUPLICATE_ID')
        self.contract = load_json(EXAMPLE)
        self.contract['edges'][0]['to'] = 'missing'
        self.assertBlocked('EDGE_ENDPOINT')
        self.contract['entities'][0]['boundary'] = 'missing'
        self.assertBlocked('BOUNDARY_REF')
        self.contract['entities'][0]['source_ids'] = ['missing']
        self.assertBlocked('SOURCE_REF')

    def test_locale_parity_for_entities_edges_boundaries_and_languages(self):
        for group in ('entities', 'edges', 'boundaries'):
            contract = copy.deepcopy(self.contract)
            contract['locales']['ja'][group].pop(next(iter(contract['locales']['ja'][group])))
            self.assertBlocked('LOCALE_PARITY', contract)
        self.contract['locales']['ja']['entities']['invented'] = 'extra label'
        self.assertBlocked('LOCALE_PARITY')
        self.contract['brief']['languages'].append('fr')
        self.assertBlocked('LOCALE_PARITY')

    def test_source_hash_drift_is_not_repaired_by_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in self.contract['sources']:
                path = root/source['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT/source['path']).read_bytes())
            frozen = json.dumps(self.contract, sort_keys=True)
            historical = root/self.contract['sources'][0]['path']
            initial = historical.read_bytes()
            (root/self.contract['sources'][1]['path']).write_text('New current integration', encoding='utf-8')
            self.assertBlocked('SOURCE_HASH', root=root)
            self.assertEqual(json.dumps(self.contract, sort_keys=True), frozen)
            self.assertEqual(historical.read_bytes(), initial)
            # Explicitly reviewed new integration leaves the historical record intact.
            current = self.contract['sources'][1]
            current['revision'] = 'fictional-integration-v2'
            current['sha256'] = hashlib.sha256((root/current['path']).read_bytes()).hexdigest()
            self.contract['provenance']['current_integration_revision'] = current['revision']
            self.assertEqual(validate(self.contract, root), [])
            self.assertEqual(self.contract['sources'][0], load_json(EXAMPLE)['sources'][0])

    def test_missing_source_and_source_scope_revision(self):
        self.contract['sources'][1]['path'] = 'missing-source.md'
        self.assertBlocked('SOURCE_PATH')
        self.contract['sources'][1]['revision'] = 'wrong'
        self.assertBlocked('PROVENANCE')
        self.contract['sources'].pop(0)
        self.assertBlocked('PROVENANCE')

    def test_paths_stay_inside_explicit_root(self):
        for value in ('../outside', '/tmp/outside', 'https://example.com/source', 'a\\b', './source'):
            contract = copy.deepcopy(self.contract)
            contract['sources'][0]['path'] = value
            self.assertBlocked('SOURCE_PATH', contract)
            contract['artifacts'][0]['path'] = value
            self.assertBlocked('ARTIFACT_PATH', contract)
    def test_source_symlink_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            symlink_or_skip(self, Path(tmp)/'escape', outside, target_is_directory=True)
            self.contract['sources'][0]['path'] = 'escape/source.md'
            self.assertBlocked('SOURCE_PATH', root=Path(tmp))

    def test_output_symlink_cannot_overwrite_a_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in self.contract['sources']:
                path = root/source['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT/source['path']).read_bytes())
            symlink_or_skip(self, root/self.contract['artifacts'][0]['path'], root/self.contract['sources'][0]['path'])
            self.assertBlocked('ARTIFACT_PATH', root=root)

    def test_semantic_authority_and_policy_bypasses(self):
        self.contract['boundaries'][1]['can_authorize'] = True
        self.assertBlocked('AUTHORITY')
        self.contract = load_json(EXAMPLE)
        self.contract['entities'][4]['boundary'] = 'semantic'
        self.assertBlocked('AUTHORITY')
        self.contract = load_json(EXAMPLE)
        self.contract['edges'][2]['kind'] = 'control'
        self.assertBlocked('AUTHORITY')
        self.contract = load_json(EXAMPLE)
        self.contract['edges'][4]['from'] = 'typed'
        self.assertBlocked('POLICY_BYPASS')
        self.contract = load_json(EXAMPLE)
        self.contract['edges'] = [e for e in self.contract['edges'] if e['id'] != 'rules_gate']
        self.assertBlocked('POLICY_GATE')
        self.contract = load_json(EXAMPLE)
        self.contract['entities'][3]['assertion'] = 'assumption'
        self.assertBlocked('POLICY_GATE')

    def test_generic_state_view_does_not_invent_authorization(self):
        self.contract['intent'] = 'state'
        for entity in self.contract['entities']:
            entity['role'] = 'state'
        for boundary in self.contract['boundaries']:
            boundary['can_authorize'] = False
        for edge in self.contract['edges']:
            edge['kind'] = 'data'
        self.assertEqual(validate(self.contract, ROOT), [])

    def test_generic_state_control_edges_do_not_imply_authorization(self):
        self.contract['intent'] = 'state'
        for entity in self.contract['entities']:
            entity['role'] = 'state'
            entity['boundary'] = 'context'
        for boundary in self.contract['boundaries']:
            boundary['can_authorize'] = False
        for edge in self.contract['edges']:
            edge['kind'] = 'control'
        self.assertEqual(validate(self.contract, ROOT), [])
        self.contract['entities'][0]['boundary'] = 'semantic'
        self.assertBlocked('AUTHORITY')

    def test_read_only_classifier_without_dispatch_passes_all_factual_intents(self):
        contract = load_json(ROOT/'tests/fixtures/classifier-only.json')
        self.assertEqual({e['role'] for e in contract['entities']}, {'input', 'classifier', 'typed_result'})
        self.assertFalse(any(b['can_authorize'] for b in contract['boundaries']))
        for intent in ('software_architecture', 'dataflow', 'state', 'policy'):
            with self.subTest(intent=intent):
                contract['intent'] = intent
                self.assertEqual(validate(contract, ROOT), [])

    def test_classifier_cannot_authorize_or_control_outputs(self):
        contract = load_json(ROOT/'tests/fixtures/classifier-only.json')
        contract['boundaries'][0]['can_authorize'] = True
        self.assertBlocked('AUTHORITY', contract)
        self.assertBlocked('POLICY_GATE', contract)
        contract = load_json(ROOT/'tests/fixtures/classifier-only.json')
        contract['edges'][1]['kind'] = 'control'
        self.assertBlocked('AUTHORITY', contract)

    def test_missing_policy_gate_is_still_blocked_for_protected_outcomes(self):
        self.contract['entities'] = [e for e in self.contract['entities'] if e['role'] != 'policy_gate']
        self.assertBlocked('POLICY_GATE')
        self.assertBlocked('POLICY_BYPASS')

    def test_generic_policy_gate_does_not_invent_a_semantic_classifier(self):
        self.contract['intent'] = 'policy'
        for entity in self.contract['entities']:
            if entity['role'] in {'classifier', 'typed_result'}:
                entity['role'] = 'component'
        self.assertEqual(validate(self.contract, ROOT), [])
        self.contract['edges'] = [e for e in self.contract['edges'] if e['id'] != 'rules_gate']
        self.assertBlocked('POLICY_GATE')

    def test_greenfield_explicitly_has_no_historical_baseline(self):
        self.contract['provenance']['historical_source_revision'] = None
        self.contract['sources'] = [s for s in self.contract['sources'] if s['scope'] != 'historical']
        self.assertEqual(validate(self.contract, ROOT), [])
        self.contract['provenance']['historical_source_revision'] = 'invented-baseline'
        self.assertBlocked('PROVENANCE')

    def test_no_history_cannot_hide_historical_source_records_or_missing_current_source(self):
        self.contract['provenance']['historical_source_revision'] = None
        self.assertBlocked('PROVENANCE')
        self.contract['sources'] = [s for s in self.contract['sources'] if s['scope'] == 'historical']
        self.assertBlocked('PROVENANCE')

    def test_free_text_only_spec_bug_is_blocked_before_any_plan(self):
        self.contract['brief']['use'] = 'Explain the software architecture; build a physical tabletop instrument'
        self.assertBlocked('PURPOSE_CHANGED')
        with self.assertRaisesRegex(ValueError, 'PURPOSE_CHANGED'):
            render_plan(self.contract, ROOT)
        # Correct the purpose rather than regenerating a hash of the contradiction.
        self.contract['brief']['use'] = load_json(EXAMPLE)['brief']['use']
        self.assertEqual(validate(self.contract, ROOT), [])

    def test_typed_rendering_directions_cannot_contradict_authorized_intent(self):
        self.contract['rendering']['directives'] = ['physical_mechanism', 'isometric_machine']
        self.assertBlocked('RENDER_MISMATCH')
        with self.assertRaisesRegex(ValueError, 'RENDER_MISMATCH'):
            render_plan(self.contract, ROOT)
        self.contract['rendering']['directives'] = ['labelled_entities', 'directed_edges', 'boundaries']
        self.assertEqual(validate(self.contract, ROOT), [])

    def test_unresolved_purpose_needs_clarification_not_lint_approval(self):
        self.contract['rendering']['ambiguity'] = 'unresolved'
        self.assertBlocked('RENDER_AMBIGUOUS')
        with self.assertRaisesRegex(ValueError, 'RENDER_AMBIGUOUS'):
            render_plan(self.contract, ROOT)
        self.contract['rendering']['ambiguity'] = 'clear'
        self.assertEqual(validate(self.contract, ROOT), [])

    def test_render_plan_uses_only_typed_directives_and_not_free_text_instructions(self):
        self.contract['brief']['use'] = 'Explain the software architecture; build a physical tabletop instrument'
        self.contract['rendering']['purpose_sha256'] = purpose_hash(self.contract)
        # Deliberately dishonest rebinding cannot turn prose into producer directives.
        # Lint is not an NLP/semantic truth check: this limitation is documented.
        plan = render_plan(self.contract, ROOT)
        self.assertNotIn('brief', plan)
        self.assertNotIn('physical tabletop instrument', json.dumps(plan))
        self.assertEqual(plan['view']['type'], 'labelled_graph')
        self.assertEqual(plan['directives'], ['boundaries', 'directed_edges', 'labelled_entities'])
        self.assertNotIn('physical_mechanism', plan['directives'])

    def test_cli_render_plan_is_json_or_blocks_with_no_output(self):
        script = ROOT/'scripts/validate_contract.py'
        valid = subprocess.run([sys.executable, str(script), str(EXAMPLE), '--root', str(ROOT), '--render-plan'],
                               capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(json.loads(valid.stdout), render_plan(self.contract, ROOT))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'contradiction.json'
            self.contract['brief']['use'] = 'Explain architecture; build a physical tabletop instrument'
            path.write_text(json.dumps(self.contract), encoding='utf-8')
            bad = subprocess.run([sys.executable, str(script), str(path), '--root', str(ROOT), '--render-plan'],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            self.assertEqual(bad.stdout, '')
            self.assertIn('PURPOSE_CHANGED', bad.stderr)

    def test_artifact_paths_formats_locales(self):
        self.contract['artifacts'][0]['path'] = self.contract['sources'][0]['path']
        self.assertBlocked('ARTIFACT_PATH')
        self.contract['artifacts'][0]['format'] = 'png'
        self.assertBlocked('ARTIFACT_FORMAT')
        self.contract['artifacts'][0]['locale'] = 'fr'
        self.assertBlocked('ARTIFACT_LOCALE')
        self.contract = load_json(EXAMPLE)
        self.contract['artifacts'][1]['path'] = self.contract['artifacts'][0]['path']
        self.assertBlocked('ARTIFACT_PATH')

    def test_required_independent_review_gates(self):
        for name in self.contract['review_gates']:
            contract = copy.deepcopy(self.contract)
            contract['review_gates'].pop(name)
            self.assertBlocked('SCHEMA', contract)
            contract = copy.deepcopy(self.contract)
            contract['review_gates'][name]['required'] = False
            self.assertBlocked('SCHEMA', contract)
        self.contract['review_gates']['publication_approval']['status'] = 'approved'
        self.assertBlocked('REVIEW_GATE')
        self.contract['review_gates']['publication_approval']['reviewer'] = 'Human reviewer'
        self.assertBlocked('REVIEW_GATE')

    def test_strict_json_and_cli_exit_codes(self):
        script = ROOT/'scripts/validate_contract.py'
        with tempfile.TemporaryDirectory() as tmp:
            valid = subprocess.run([sys.executable, str(script), str(EXAMPLE), '--root', str(ROOT)],
                                   cwd=tmp, capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn('structural contract checks only', valid.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp)/'bad.json'
            for content in ('{"x":1,"x":2}', '{"x":NaN}', '{broken'):
                bad.write_text(content, encoding='utf-8')
                result = subprocess.run([sys.executable, str(script), str(bad)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('INPUT_ERROR', result.stderr)


class ArtifactTests(unittest.TestCase):
    def test_committed_svg_exists_before_reproduction_and_matches_contract(self):
        contract = load_json(EXAMPLE)
        for artifact in contract['artifacts']:
            path = ROOT/artifact['path']
            self.assertTrue(path.is_file(), f'Missing committed output: {path}')
            self.assertEqual(path.read_bytes(), render_example.render(contract, artifact['locale']))
            svg = ET.fromstring(path.read_bytes())
            ns = '{http://www.w3.org/2000/svg}'
            self.assertEqual(svg.tag, ns+'svg')
            self.assertEqual(svg.attrib['role'], 'img')
            self.assertEqual(svg.attrib['aria-labelledby'], 'title description')
            labels = contract['locales'][artifact['locale']]
            self.assertEqual(svg.find(ns+'title').text, labels['title'])
            self.assertEqual(svg.find(ns+'desc').text, labels['description'])
            for group, attr in (('entities', 'data-entity-id'), ('edges', 'data-edge-id'), ('boundaries', 'data-boundary-id')):
                nodes = {n.attrib[attr]: n for n in svg.iter() if attr in n.attrib}
                self.assertEqual(set(nodes), {item['id'] for item in contract[group]})
                for identifier, node in nodes.items():
                    self.assertEqual(node.find(ns+'text').text, labels[group][identifier])
            edge_nodes = {n.attrib['data-edge-id']: n for n in svg.iter() if 'data-edge-id' in n.attrib}
            for edge in contract['edges']:
                node = edge_nodes[edge['id']]
                self.assertEqual(node.attrib['data-from'], edge['from'])
                self.assertEqual(node.attrib['data-to'], edge['to'])
            for node in svg.iter():
                self.assertNotIn(node.tag, {ns+'script', ns+'foreignObject', ns+'animate'})
                self.assertFalse(any(k.startswith('on') or k.endswith('href') for k in node.attrib))

    def test_check_does_not_regenerate_missing_or_stale_outputs(self):
        from unittest.mock import patch
        contract = load_json(EXAMPLE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in contract['sources']:
                path = root/source['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT/source['path']).read_bytes())
            with patch.object(render_example, 'ROOT', root), redirect_stderr(io.StringIO()):
                self.assertEqual(render_example.main(['--check']), 1)
                self.assertFalse((root/contract['artifacts'][0]['path']).exists())
                for artifact in contract['artifacts']:
                    (root/artifact['path']).write_bytes(render_example.render(contract, artifact['locale']))
                stale = root/contract['artifacts'][1]['path']
                stale.write_bytes(b'stale')
                self.assertEqual(render_example.main(['--check']), 1)
                self.assertEqual(stale.read_bytes(), b'stale')

    def test_missing_svg_diagnostic_handles_an_aliased_source_root(self):
        from unittest.mock import patch
        contract = load_json(EXAMPLE)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_root = base/'content'
            for source in contract['sources']:
                path = real_root/source['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT/source['path']).read_bytes())
            alias_root = base/'alias'
            symlink_or_skip(self, alias_root, real_root, target_is_directory=True)
            with patch.object(render_example, 'ROOT', alias_root), redirect_stderr(io.StringIO()) as diagnostics:
                self.assertEqual(render_example.main(['--check']), 1)
                self.assertIn('architecture.en.svg', diagnostics.getvalue())
                self.assertFalse(any(real_root.rglob('*.svg')))

    def test_renderer_blocks_invalid_contract_before_writing(self):
        from unittest.mock import patch
        bad = load_json(ROOT/'tests/fixtures/bad-physical-instrument.json')
        with tempfile.TemporaryDirectory() as tmp, patch.object(render_example, 'ROOT', Path(tmp)), \
                patch.object(render_example, 'load_json', return_value=bad), redirect_stderr(io.StringIO()) as diagnostics:
            self.assertEqual(render_example.main([]), 1)
            self.assertIn('VIEW_MISMATCH', diagnostics.getvalue())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_fixed_renderer_rejects_changed_topology_even_with_same_ids(self):
        from unittest.mock import patch
        contract = load_json(EXAMPLE)
        contract['edges'][0]['from'] = 'rules'  # Structurally valid data; fixed route would be wrong.
        self.assertEqual(validate(contract, ROOT), [])
        with patch.object(render_example, 'load_json', return_value=contract), redirect_stderr(io.StringIO()):
            self.assertEqual(render_example.main(['--check']), 1)

    def test_renderer_blocks_free_text_purpose_change_before_writing(self):
        from unittest.mock import patch
        contract = load_json(EXAMPLE)
        contract['brief']['use'] = 'Explain architecture; build a physical tabletop instrument'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in contract['sources']:
                path = root/source['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT/source['path']).read_bytes())
            with patch.object(render_example, 'ROOT', root), patch.object(render_example, 'load_json', return_value=contract), \
                    redirect_stderr(io.StringIO()) as diagnostics:
                self.assertEqual(render_example.main([]), 1)
                self.assertIn('PURPOSE_CHANGED', diagnostics.getvalue())
                self.assertFalse(any(root.rglob('*.svg')))

    def test_demo_renderer_does_not_ignore_physical_render_plan(self):
        from unittest.mock import patch
        contract = load_json(EXAMPLE)
        contract['intent'] = 'physical_mechanism'
        contract['view'] = {'type': 'physical_mechanism', 'style': 'isometric_machine',
                            'physical_metaphor_requested': True}
        contract['rendering']['directives'] = ['physical_mechanism', 'isometric_machine']
        contract['brief']['metaphors'] = ['An explicitly requested separate physical teaching view.']
        self.assertEqual(validate(contract, ROOT), [])
        with patch.object(render_example, 'load_json', return_value=contract), redirect_stderr(io.StringIO()):
            self.assertEqual(render_example.main(['--check']), 1)

    def test_skill_metadata_and_portable_reference(self):
        skill = ROOT/'skills/diagram-contract/SKILL.md'
        text = skill.read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\n'))
        header = text.split('---', 2)[1]
        fields = dict(line.split(': ', 1) for line in header.strip().splitlines())
        self.assertEqual(fields['name'], skill.parent.name)
        self.assertRegex(fields['name'], r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        self.assertLessEqual(len(fields['name']), 64)
        self.assertTrue(0 < len(fields['description']) <= 1024)
        self.assertLessEqual(len(fields['compatibility']), 500)
        self.assertTrue((skill.parent/'references/contract-guide.md').is_file())


if __name__ == '__main__':
    unittest.main()
