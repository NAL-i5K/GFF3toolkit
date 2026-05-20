import io
import unittest

from gff3tool.bin import gff3_sort


def _feature(line_raw, line_index, seqid='chr1', start=1, end=2, strand='+', feature_type='exon'):
    return {
        'line_raw': line_raw,
        'line_index': line_index,
        'seqid': seqid,
        'start': start,
        'end': end,
        'strand': strand,
        'type': feature_type,
        'attributes': {'ID': line_raw},
        'children': [],
    }


class TestGff3SortFunctions(unittest.TestCase):
    def test_position_sort_orders_by_numeric_seqid_and_start(self):
        lines = [
            _feature('chr10_b', 2, seqid='chr10', start=9),
            _feature('chr2_b', 1, seqid='chr2', start=7),
            _feature('chr2_a', 0, seqid='chr2', start=3),
        ]

        result = gff3_sort.PositionSort(lines, reference=False)

        self.assertEqual([line['line_raw'] for line in result], ['chr2_a', 'chr2_b', 'chr10_b'])

    def test_position_sort_honors_reference_order(self):
        lines = [
            _feature('scafB', 1, seqid='scaffoldB', start=4),
            _feature('scafA', 0, seqid='scaffoldA', start=2),
            _feature('scafB_2', 2, seqid='scaffoldB', start=8),
        ]

        result = gff3_sort.PositionSort(lines, reference=True)

        self.assertEqual([line['line_raw'] for line in result], ['scafB', 'scafB_2', 'scafA'])

    def test_position_sort_exits_when_seqid_lacks_numeric_suffix(self):
        lines = [_feature('bad', 0, seqid='chrX', start=1)]

        with self.assertRaises(SystemExit):
            gff3_sort.PositionSort(lines, reference=False)

    def test_strand_sort_orders_plus_by_start(self):
        lines = [
            _feature('later', 1, start=9, end=12, strand='+'),
            _feature('earlier', 0, start=3, end=5, strand='+'),
        ]

        result = gff3_sort.StrandSort(lines)

        self.assertEqual([line['line_raw'] for line in result], ['earlier', 'later'])

    def test_strand_sort_orders_minus_by_end_descending(self):
        lines = [
            _feature('small_end', 1, start=1, end=5, strand='-'),
            _feature('large_end', 0, start=1, end=20, strand='-'),
        ]

        result = gff3_sort.StrandSort(lines)

        self.assertEqual([line['line_raw'] for line in result], ['large_end', 'small_end'])

    def test_strand_sort_returns_none_for_mixed_strands(self):
        lines = [
            _feature('plus', 0, start=1, end=2, strand='+'),
            _feature('minus', 1, start=3, end=4, strand='-'),
        ]

        result = gff3_sort.StrandSort(lines)

        self.assertIsNone(result)

    def test_type_sort_uses_type_rank_then_coordinate(self):
        lines = [
            _feature('utr', 0, start=3, end=6, feature_type='UTR'),
            _feature('exon', 1, start=4, end=8, feature_type='exon'),
            _feature('cds', 2, start=2, end=10, feature_type='CDS'),
        ]

        result = gff3_sort.TypeSort(lines, {'CDS': 1, 'exon': 2})

        self.assertEqual([line['line_raw'] for line in result], ['cds', 'exon', 'utr'])

    def test_type_sort_reverse_uses_end_position(self):
        lines = [
            _feature('cds', 0, start=2, end=10, feature_type='CDS'),
            _feature('exon', 1, start=4, end=8, feature_type='exon'),
        ]

        result = gff3_sort.TypeSort(lines, {'CDS': 1, 'exon': 2}, reverse=True)

        self.assertEqual([line['line_raw'] for line in result], ['cds', 'exon'])

    def test_two_parent_rewrites_parent_attribute(self):
        third = _feature('chr1\tsrc\texon\t1\t2\t.\t+\t.\tID=ex1;Parent=old\n', 0)
        third['attributes'] = {'ID': 'ex1', 'Parent': ['tx1', 'tx2']}

        result = gff3_sort.TwoParent('tx2', third)

        self.assertIn('Parent=tx2', result)
        self.assertTrue(result.endswith('\n'))

    def test_write_out_by_level_writes_sorted_children_recursively(self):
        child_b = _feature('child_b\n', 2, start=5, feature_type='exon')
        child_a = _feature('child_a\n', 1, start=1, feature_type='CDS')
        root = _feature('root\n', 0, feature_type='gene')
        root['children'] = [child_b, child_a]
        handle = io.StringIO()

        remaining = gff3_sort.write_out_by_level(
            handle,
            root,
            {'CDS': 1, 'exon': 2},
            {0, 1, 2},
        )

        self.assertEqual(handle.getvalue(), 'root\nchild_a\nchild_b\n')
        self.assertEqual(remaining, set())


if __name__ == '__main__':
    unittest.main()