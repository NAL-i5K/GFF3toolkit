import io
import unittest
from argparse import Namespace
from unittest import mock

from gff3tool.bin import gff3_fix


class TestGff3FixCli(unittest.TestCase):
    def test_script_main_exits_when_qc_report_missing(self):
        args = Namespace(qc_report=None, gff='input.gff3', output_gff='out.gff3')

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('argparse.ArgumentParser.print_help') as print_help, \
            self.assertRaises(SystemExit):
            gff3_fix.script_main()

        print_help.assert_called_once()

    def test_script_main_exits_when_gff_missing(self):
        args = Namespace(qc_report='report.txt', gff=None, output_gff='out.gff3')

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('argparse.ArgumentParser.print_help') as print_help, \
            self.assertRaises(SystemExit):
            gff3_fix.script_main()

        print_help.assert_called_once()

    def test_script_main_parses_qc_report_and_calls_fix_main(self):
        args = Namespace(qc_report='report.txt', gff='input.gff3', output_gff='out.gff3')
        report_content = (
            'Line_num\tError_code\tError_level\tError_tag\n'
            "['Line 2', 'Line 4']\tEmr0001\tError\ttag1\n"
            "['Line 3']\tEsf0003\tWarning\ttag2\n"
            'malformed line\n'
        )
        gff3 = object()

        def open_side_effect(path, mode='r', *args, **kwargs):
            if path == 'report.txt':
                return io.StringIO(report_content)
            raise AssertionError(path)

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('builtins.open', side_effect=open_side_effect), \
            mock.patch.object(gff3_fix, 'Gff3', autospec=True, return_value=gff3), \
            mock.patch.object(gff3_fix.gff3_fix.fix, 'main', autospec=True) as fix_main:
            gff3_fix.script_main()

        fix_main.assert_called_once_with(
            gff3=gff3,
            output_gff='out.gff3',
            error_dict={'Emr0001': [[2, 4]], 'Esf0003': [[3]]},
            line_num_dict={2: {'Emr0001': 'Error'}, 4: {'Emr0001': 'Error'}, 3: {'Esf0003': 'Warning'}},
            logger=mock.ANY,
        )

    def test_script_main_exits_when_gff_cannot_be_read(self):
        args = Namespace(qc_report='report.txt', gff='input.gff3', output_gff='out.gff3')

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('builtins.open', return_value=io.StringIO('header\n')), \
            mock.patch.object(gff3_fix, 'Gff3', autospec=True, side_effect=OSError), \
            self.assertRaises(SystemExit) as exc:
            gff3_fix.script_main()

        self.assertEqual(exc.exception.code, 1)


if __name__ == '__main__':
    unittest.main()