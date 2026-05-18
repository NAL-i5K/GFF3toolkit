import tempfile
import unittest
from argparse import Namespace
from unittest import mock

from gff3tool.bin import gff3_sort


class TestGff3SortCli(unittest.TestCase):
    def test_script_main_exits_when_gff_missing(self):
        args = Namespace(
            gff_file=None,
            output_gff='out.gff3',
            sort_template=None,
            isoform_sort=False,
            reference=False,
        )

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('argparse.ArgumentParser.print_help') as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_sort.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_disables_isoform_sort_without_template(self):
        args = Namespace(
            gff_file='input.gff3',
            output_gff='sorted.gff3',
            sort_template=None,
            isoform_sort=True,
            reference=False,
        )

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch.object(gff3_sort, 'main', autospec=True) as main_mock:
            gff3_sort.script_main()

        main_mock.assert_called_once_with(
            'input.gff3',
            output='sorted.gff3',
            isoform_sort=False,
            sorting_order=None,
            logger=mock.ANY,
            reference=False,
        )

    def test_script_main_reads_sort_template(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as handle:
            handle.write('gene pseudogene\n')
            handle.write('mRNA\n')
            template_path = handle.name

        args = Namespace(
            gff_file='input.gff3',
            output_gff='sorted.gff3',
            sort_template=template_path,
            isoform_sort=False,
            reference=False,
        )

        try:
            with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
                mock.patch.object(gff3_sort, 'main', autospec=True) as main_mock:
                gff3_sort.script_main()
        finally:
            import os
            os.unlink(template_path)

        main_mock.assert_called_once_with(
            'input.gff3',
            output='sorted.gff3',
            isoform_sort=False,
            sorting_order={'gene': 1, 'pseudogene': 1, 'mRNA': 2},
            logger=mock.ANY,
            reference=False,
        )

    def test_script_main_exits_when_template_unreadable(self):
        args = Namespace(
            gff_file='input.gff3',
            output_gff='sorted.gff3',
            sort_template='missing-template.txt',
            isoform_sort=False,
            reference=False,
        )

        with mock.patch('argparse.ArgumentParser.parse_args', return_value=args), \
            mock.patch('builtins.open', side_effect=OSError), \
            self.assertRaises(SystemExit) as exc:
            gff3_sort.script_main()

        self.assertEqual(exc.exception.code, 1)


if __name__ == '__main__':
    unittest.main()