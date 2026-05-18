import logging
import unittest
from unittest import mock

from gff3tool.lib.single_feature import single_feature


class DummyGff:
    def __init__(self, lines=None, descendants=None):
        self.lines = lines or []
        self.descendants = descendants or {}
        self.line_errors = []

    def collect_descendants(self, line):
        return self.descendants.get(id(line), [])

    def add_line_error(self, line, error, log_level=None):
        self.line_errors.append((line, error, log_level))


def _feature(line_id, line_index, feature_type, attributes=None, children=None, strand='+'):
    return {
        'line_type': 'feature',
        'line_raw': line_id,
        'line_index': line_index,
        'type': feature_type,
        'attributes': attributes or {'ID': line_id},
        'children': children or [],
        'line_status': 'active',
        'strand': strand,
    }


class TestSingleFeature(unittest.TestCase):
    def test_fix_pseudogene_rewrites_transcript_and_descendants(self):
        nested = _feature('nested', 4, 'five_prime_UTR')
        cds = _feature('cds1', 2, 'CDS')
        exon = _feature('exon1', 3, 'exon')
        mrna = _feature('tx1', 1, 'mRNA', children=[cds, exon])
        root = _feature('gene1', 0, 'pseudogene', children=[mrna])
        gff = DummyGff(lines=[root], descendants={id(cds): [nested], id(exon): []})

        single_feature.FIX_PSEUDOGENE(gff)

        self.assertEqual(mrna['type'], 'pseudogenic_transcript')
        self.assertEqual(cds['line_status'], 'removed')
        self.assertEqual(exon['type'], 'pseudogenic_exon')
        self.assertEqual(nested['line_status'], 'removed')

    def test_fix_pseudogene_handles_missing_attributes_without_crashing(self):
        broken = {
            'line_type': 'feature',
            'line_raw': 'broken',
            'line_index': 0,
            'type': 'gene',
        }
        gff = DummyGff(lines=[broken])

        single_feature.FIX_PSEUDOGENE(gff)

        self.assertEqual(gff.line_errors, [])

    def test_check_pseudogene_reports_non_pseudogene_feature_with_matching_attribute(self):
        gff = DummyGff()
        line = _feature('gene1', 0, 'gene', attributes={'ID': 'gene1', 'Note': 'possible pseudogene'})

        result = single_feature.check_pseudogene(gff, line)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['eCode'], 'Esf0001')
        self.assertEqual(gff.line_errors[0][1]['eCode'], 'Esf0001')
        self.assertEqual(gff.line_errors[0][2], logging.INFO)

    def test_check_strand_allows_plus_and_minus(self):
        gff = DummyGff()

        self.assertIsNone(single_feature.check_strand(gff, _feature('plus', 0, 'gene', strand='+')))
        self.assertIsNone(single_feature.check_strand(gff, _feature('minus', 1, 'gene', strand='-')))
        self.assertEqual(gff.line_errors, [])

    def test_check_strand_reports_legal_but_flagged_unknown_strand(self):
        gff = DummyGff()
        line = _feature('unknown', 2, 'gene', strand='?')

        result = single_feature.check_strand(gff, line)

        self.assertEqual(len(result), 1)
        self.assertIn('legal chacracter', result[0]['eTag'])
        self.assertEqual(gff.line_errors[0][1]['eCode'], 'Esf0003')

    def test_check_strand_reports_illegal_character(self):
        gff = DummyGff()
        line = _feature('bad', 3, 'gene', strand='x')

        result = single_feature.check_strand(gff, line)

        self.assertEqual(len(result), 1)
        self.assertIn('illegal chacracter', result[0]['eTag'])
        self.assertEqual(gff.line_errors[0][1]['eCode'], 'Esf0003')

    def test_check_pseudogene_gracefully_handles_missing_id(self):
        gff = DummyGff()
        line = _feature('gene1', 0, 'gene', attributes={'Note': 'pseudogene'})

        result = single_feature.check_pseudogene(gff, line)

        self.assertIsNone(result)
        self.assertEqual(gff.line_errors, [])

    def test_main_runs_fix_and_aggregates_errors(self):
        lines = [_feature('gene1', 0, 'gene')]
        gff = DummyGff(lines=lines)
        pseudogene_errors = [{'eCode': 'Esf0001'}]
        strand_errors = [{'eCode': 'Esf0003'}]

        with mock.patch.object(single_feature.function4gff, 'FIX_MISSING_ATTR', autospec=True) as fix_mock, \
            mock.patch.object(single_feature, 'FIX_PSEUDOGENE', autospec=True) as pseudo_fix_mock, \
            mock.patch.object(single_feature, 'check_pseudogene', autospec=True, return_value=pseudogene_errors), \
            mock.patch.object(single_feature, 'check_strand', autospec=True, return_value=strand_errors):
            result = single_feature.main(gff, logger=mock.Mock())

        fix_mock.assert_called_once()
        pseudo_fix_mock.assert_called_once_with(gff)
        self.assertEqual(result, pseudogene_errors + strand_errors)


if __name__ == '__main__':
    unittest.main()