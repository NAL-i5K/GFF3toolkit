import io
import os
import tempfile
import unittest

from gff3tool.lib import gff3_ID_generator


class DummyGff:
    def __init__(self, lines, descendants_map=None):
        self.lines = lines
        self._descendants_map = descendants_map or {}

    def descendants(self, root):
        return self._descendants_map.get(root['attributes']['ID'], [])


class TestGff3IdGeneratorUtilities(unittest.TestCase):
    def test_type_sort_orders_by_type_then_start(self):
        lines = [
            {
                'line_raw': 'l1',
                'start': 20,
                'end': 25,
                'type': 'mRNA',
            },
            {
                'line_raw': 'l2',
                'start': 10,
                'end': 15,
                'type': 'gene',
            },
            {
                'line_raw': 'l3',
                'start': 5,
                'end': 8,
                'type': 'unknown',
            },
        ]
        sorted_lines = gff3_ID_generator.TypeSort(lines, {'gene': 1, 'mRNA': 2})
        self.assertEqual([line['line_raw'] for line in sorted_lines], ['l2', 'l1', 'l3'])

    def test_descendants_and_levels(self):
        grandchild = {'attributes': {'ID': 'gc1'}, 'children': []}
        child = {'attributes': {'ID': 'c1'}, 'children': [grandchild]}
        root = {'attributes': {'ID': 'r1'}, 'children': [child]}

        descendants = gff3_ID_generator.descendants_list(root, 0)
        self.assertEqual([d['attributes']['ID'] for d in descendants], ['c1', 'gc1'])
        self.assertEqual(descendants[0]['level'], 0)
        self.assertEqual(descendants[1]['level'], 1)

        by_level = gff3_ID_generator.level_list(descendants)
        self.assertEqual([d['attributes']['ID'] for d in by_level[0]], ['c1'])
        self.assertEqual([d['attributes']['ID'] for d in by_level[1]], ['gc1'])

    def test_idgenerator_zero_pads(self):
        result = gff3_ID_generator.idgenerator('MODEL', 9, 4)
        self.assertEqual(result['ID'], 'MODEL0010')
        self.assertEqual(result['maxnum'], 10)

    def test_write_features_serializes_attributes(self):
        line = {
            'seqid': 'chr1',
            'source': '.',
            'type': 'gene',
            'start': 1,
            'end': 10,
            'score': '.',
            'strand': '+',
            'phase': '.',
            'attributes': {
                'ID': 'gene1',
                'Parent': ['p1', 'p2'],
            },
        }
        out = io.StringIO()
        gff3_ID_generator.write_features(line, out)
        text = out.getvalue().strip()
        self.assertIn('ID=gene1', text)
        self.assertIn('Parent=p1,p2', text)

    def test_write_gff3_writes_directives_features_and_separator(self):
        root = {
            'line_type': 'feature',
            'line_index': 0,
            'line_raw': 'root-raw',
            'seqid': 'chr1',
            'source': '.',
            'type': 'gene',
            'start': 1,
            'end': 20,
            'score': '.',
            'strand': '+',
            'phase': '.',
            'attributes': {'ID': 'gene1'},
        }
        child = {
            'line_type': 'feature',
            'line_index': 1,
            'line_raw': 'child-raw',
            'seqid': 'chr1',
            'source': '.',
            'type': 'mRNA',
            'start': 1,
            'end': 20,
            'score': '.',
            'strand': '+',
            'phase': '.',
            'attributes': {'ID': 'tx1', 'Parent': ['gene1']},
        }
        directive = {
            'line_type': 'directive',
            'line_raw': '##gff-version 3\n',
            'directive': '##gff-version',
        }
        seqreg = {
            'line_type': 'directive',
            'directive': '##sequence-region',
            'seqid': 'chr1',
            'start': 1,
            'end': 100,
        }

        gff = DummyGff([directive, seqreg, root, child], descendants_map={'gene1': [child]})

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, 'out.gff3')
            gff3_ID_generator.write_gff3(gff, out_path)
            with open(out_path, 'r', encoding='utf-8') as handle:
                content = handle.read()

        self.assertIn('##gff-version 3', content)
        self.assertIn('##sequence-region chr1 1 100', content)
        self.assertIn('ID=gene1', content)
        self.assertIn('ID=tx1;Parent=gene1', content)
        self.assertIn('###', content)

    def test_read_merge_report_parses_headers_logs_and_index(self):
        report = (
            '# comment\n'
            'Change_log\tOriginal_gene_name\tOriginal_transcript_ID\tOriginal_transcript_name\tTmp_OGSv0_ID\n'
            'simple\tgeneA\ttrA\tnameA\tMODEL0001\n'
            'simple\tgeneB\ttrB\tnameB\tNA\n'
        )

        with tempfile.NamedTemporaryFile('wb', delete=False) as fh:
            fh.write(report.encode('utf-8'))
            report_path = fh.name

        try:
            headers, logs, index_map = gff3_ID_generator.read_merge_report(None, report_path)
        finally:
            os.unlink(report_path)

        self.assertTrue(any('Change_log' in line for line in headers))
        self.assertEqual(len(logs), 2)
        self.assertEqual(index_map['MODEL0001'], [0])
        self.assertNotIn('NA', index_map)

    def test_alphabets_suffix_generates_uppercase_suffixes(self):
        values = gff3_ID_generator.alphabets_suffix(3)
        self.assertEqual(values[:4], ['A', 'B', 'C', 'D'])


if __name__ == '__main__':
    unittest.main()
