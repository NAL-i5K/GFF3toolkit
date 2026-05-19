import io
import unittest
from argparse import Namespace
from unittest import mock

from gff3tool.bin import gff3_merge


class TestGff3MergeCli(unittest.TestCase):
    def test_script_main_exits_when_gff_file1_missing(self):
        args = Namespace(
            gff_file1=None,
            gff_file2="ref.gff3",
            fasta="ref.fa",
            user_defined_file1=None,
            user_defined_file2=None,
            output_gff="merged.gff",
            report_file="report.txt",
            all=False,
            auto_assignment=True,
        )
        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("sys.stdin", stdin), \
            mock.patch("argparse.ArgumentParser.print_help") as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_merge.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_exits_when_gff_file2_missing(self):
        args = Namespace(
            gff_file1="new.gff3",
            gff_file2=None,
            fasta="ref.fa",
            user_defined_file1=None,
            user_defined_file2=None,
            output_gff="merged.gff",
            report_file="report.txt",
            all=False,
            auto_assignment=True,
        )
        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("sys.stdin", stdin), \
            mock.patch("argparse.ArgumentParser.print_help") as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_merge.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 2)

    def test_script_main_exits_on_conflicting_all_and_no_auto(self):
        args = Namespace(
            gff_file1="new.gff3",
            gff_file2="ref.gff3",
            fasta="ref.fa",
            user_defined_file1=None,
            user_defined_file2=None,
            output_gff="merged.gff",
            report_file="report.txt",
            all=True,
            auto_assignment=False,
        )

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            self.assertRaises(SystemExit) as exc:
            gff3_merge.script_main()

        self.assertEqual(exc.exception.code, 0)

    def test_script_main_parses_user_defined_files_and_calls_main(self):
        args = Namespace(
            gff_file1="new.gff3",
            gff_file2="ref.gff3",
            fasta="ref.fa",
            user_defined_file1="u1.txt",
            user_defined_file2="u2.txt",
            output_gff="out.gff3",
            report_file="report.txt",
            all=False,
            auto_assignment=True,
        )

        def open_side_effect(path, mode="r", *args, **kwargs):
            if path == "u1.txt":
                return io.StringIO("gene mRNA\ngene mRNA\n")
            if path == "u2.txt":
                return io.StringIO("gene mRNA\n")
            if path == "report.txt":
                return io.StringIO()
            raise AssertionError(path)

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("builtins.open", side_effect=open_side_effect), \
            mock.patch.object(gff3_merge, "main", autospec=True) as main_mock:
            gff3_merge.script_main()

        main_mock.assert_called_once_with(
            "new.gff3",
            "ref.gff3",
            "ref.fa",
            mock.ANY,
            "out.gff3",
            False,
            True,
            [["gene", "mRNA"]],
            [["gene", "mRNA"]],
            logger=mock.ANY,
        )

    def test_script_main_uses_default_report_and_output_names(self):
        args = Namespace(
            gff_file1="new.gff3",
            gff_file2="ref.gff3",
            fasta="ref.fa",
            user_defined_file1=None,
            user_defined_file2=None,
            output_gff=None,
            report_file=None,
            all=False,
            auto_assignment=True,
        )

        def open_side_effect(path, mode="r", *args, **kwargs):
            if path == "merge_report.txt":
                return io.StringIO()
            raise AssertionError(path)

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("builtins.open", side_effect=open_side_effect), \
            mock.patch.object(gff3_merge, "main", autospec=True) as main_mock:
            gff3_merge.script_main()

        called = main_mock.call_args
        self.assertEqual(called.args[4], "merged.gff")
        self.assertEqual(called.args[5], False)
        self.assertEqual(called.args[6], True)


if __name__ == "__main__":
    unittest.main()