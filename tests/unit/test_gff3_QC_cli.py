import io
import unittest
from argparse import Namespace
from unittest import mock

from gff3tool.bin import gff3_QC


class TestGff3QcCli(unittest.TestCase):
    def test_script_main_exits_when_gff_missing_and_no_stdin(self):
        args = Namespace(
            gff=None,
            fasta='ref.fa',
            noncanonical_gene=False,
            initial_phase=False,
            allowed_num_of_n=0,
            check_n_feature_types=['CDS'],
            output=None,
            statistic=None,
        )

        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('sys.stdin', stdin), \
            mock.patch('argparse.ArgumentParser.print_help') as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_QC.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_exits_when_fasta_missing_and_no_stdin(self):
        args = Namespace(
            gff='input.gff3',
            fasta=None,
            noncanonical_gene=False,
            initial_phase=False,
            allowed_num_of_n=0,
            check_n_feature_types=['CDS'],
            output=None,
            statistic=None,
        )

        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('sys.stdin', stdin), \
            mock.patch('argparse.ArgumentParser.print_help') as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_QC.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_noncanonical_skips_phase_and_writes_default_reports(self):
        args = Namespace(
            gff='input.gff3',
            fasta='ref.fa',
            noncanonical_gene=True,
            initial_phase=False,
            allowed_num_of_n=0,
            check_n_feature_types=['CDS'],
            output=None,
            statistic=None,
        )
        gff3 = mock.Mock()
        gff3.check_parent_boundary.return_value = True
        extract_errors = [{'line_num': ['Line 2'], 'eCode': 'Emr0001', 'error_level': 'Error', 'eTag': 'internal'}]
        intra_errors = [{'line_num': ['Line 3'], 'eCode': 'Ema0006', 'error_level': 'Warning', 'eTag': 'intra'}]
        inter_errors = [{'line_num': ['Line 4'], 'eCode': 'Emr0002', 'error_level': 'Error', 'eTag': 'inter'}]
        single_errors = [{'line_num': ['Line 5'], 'eCode': 'Esf0003', 'error_level': 'Error', 'eTag': 'single'}]
        report_handle = io.StringIO()
        stat_handle = io.StringIO()

        def open_side_effect(path, mode='r', *args, **kwargs):
            if path == 'report.txt':
                return report_handle
            if path == 'statistic.txt':
                return stat_handle
            raise AssertionError(path)

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch.object(gff3_QC, 'Gff3', autospec=True, return_value=gff3), \
            mock.patch.object(gff3_QC.function4gff, 'FIX_MISSING_ATTR', autospec=True) as fix_missing, \
            mock.patch.object(gff3_QC.function4gff, 'extract_internal_detected_errors', autospec=True, return_value=extract_errors), \
            mock.patch.object(gff3_QC.intra_model, 'main', autospec=True, return_value=intra_errors), \
            mock.patch.object(gff3_QC.inter_model, 'main', autospec=True, return_value=inter_errors), \
            mock.patch.object(gff3_QC.single_feature, 'main', autospec=True, return_value=single_errors), \
            mock.patch('builtins.open', side_effect=open_side_effect):
            gff3_QC.script_main()

        gff3.check_phase.assert_not_called()
        gff3.check_reference.assert_called_once_with(
            fasta_external='ref.fa',
            check_n=True,
            allowed_num_of_n=0,
            feature_types=['CDS'],
        )
        fix_missing.assert_called_once_with(gff3, logger=mock.ANY)
        self.assertIn('Line_num\tError_code\tError_level\tError_tag', report_handle.getvalue())
        self.assertIn('Emr0001', report_handle.getvalue())
        self.assertIn('Esf0003', report_handle.getvalue())
        self.assertIn('Error_code\tNumber_of_problematic_models\tError_level\tError_tag', stat_handle.getvalue())
        self.assertIn('Esf0003', stat_handle.getvalue())

    def test_script_main_runs_phase_check_for_canonical_models(self):
        args = Namespace(
            gff='input.gff3',
            fasta='ref.fa',
            noncanonical_gene=False,
            initial_phase=True,
            allowed_num_of_n=0,
            check_n_feature_types=['CDS'],
            output='qc.txt',
            statistic='stats.txt',
        )
        gff3 = mock.Mock()
        gff3.check_parent_boundary.return_value = True

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch.object(gff3_QC, 'Gff3', autospec=True, return_value=gff3), \
            mock.patch.object(gff3_QC.function4gff, 'FIX_MISSING_ATTR', autospec=True), \
            mock.patch.object(gff3_QC.function4gff, 'extract_internal_detected_errors', autospec=True, return_value=[]), \
            mock.patch.object(gff3_QC.intra_model, 'main', autospec=True, return_value=[]), \
            mock.patch.object(gff3_QC.inter_model, 'main', autospec=True, return_value=[]), \
            mock.patch.object(gff3_QC.single_feature, 'main', autospec=True, return_value=[]), \
            mock.patch('builtins.open', side_effect=[io.StringIO(), io.StringIO()]):
            gff3_QC.script_main()

        gff3.check_phase.assert_called_once_with(True)

    def test_script_main_exits_early_when_parent_boundary_fails(self):
        args = Namespace(
            gff='input.gff3',
            fasta='ref.fa',
            noncanonical_gene=False,
            initial_phase=False,
            allowed_num_of_n=0,
            check_n_feature_types=['CDS'],
            output=None,
            statistic=None,
        )
        gff3 = mock.Mock()
        gff3.check_parent_boundary.return_value = False

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch.object(gff3_QC, 'Gff3', autospec=True, return_value=gff3), \
            self.assertRaises(SystemExit):
            gff3_QC.script_main()

        gff3.check_unresolved_parents.assert_not_called()


if __name__ == '__main__':
    unittest.main()