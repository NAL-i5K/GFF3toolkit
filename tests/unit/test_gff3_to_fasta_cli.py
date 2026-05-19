import io
import unittest
from argparse import Namespace
from unittest import mock

from gff3tool.bin import gff3_to_fasta


class TestGff3ToFastaCli(unittest.TestCase):
    def test_script_main_exits_when_gff_missing(self):
        args = Namespace(
            gff=None,
            fasta="ref.fa",
            embedded_fasta=False,
            sequence_type="cds",
            user_defined=None,
            defline="simple",
            output_prefix="out",
            quality_control=True,
        )
        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("sys.stdin", stdin), \
            mock.patch("argparse.ArgumentParser.print_help") as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_exits_when_fasta_missing_without_embedded(self):
        args = Namespace(
            gff="input.gff3",
            fasta=None,
            embedded_fasta=False,
            sequence_type="cds",
            user_defined=None,
            defline="simple",
            output_prefix="out",
            quality_control=True,
        )
        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("sys.stdin", stdin), \
            mock.patch("argparse.ArgumentParser.print_help") as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_requires_user_defined_with_user_defined_type(self):
        args = Namespace(
            gff="input.gff3",
            fasta="ref.fa",
            embedded_fasta=False,
            sequence_type="user_defined",
            user_defined=None,
            defline="simple",
            output_prefix="out",
            quality_control=True,
        )

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("argparse.ArgumentParser.print_help") as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_exits_when_defline_missing(self):
        args = Namespace(
            gff="input.gff3",
            fasta="ref.fa",
            embedded_fasta=False,
            sequence_type="cds",
            user_defined=None,
            defline=None,
            output_prefix="out",
            quality_control=True,
        )
        stdin = mock.Mock()
        stdin.isatty.return_value = True

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch("sys.stdin", stdin), \
            mock.patch("argparse.ArgumentParser.print_help") as print_help, \
            self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.script_main()

        print_help.assert_called_once()
        self.assertEqual(exc.exception.code, 1)

    def test_script_main_calls_main_with_parsed_args(self):
        args = Namespace(
            gff="input.gff3",
            fasta="ref.fa",
            embedded_fasta=True,
            sequence_type="cds",
            user_defined=None,
            defline="complete",
            output_prefix="out",
            quality_control=False,
        )

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch.object(gff3_to_fasta, "main", autospec=True) as main_mock:
            gff3_to_fasta.script_main()

        main_mock.assert_called_once_with(
            "input.gff3",
            "ref.fa",
            True,
            "cds",
            None,
            "complete",
            False,
            "out",
            mock.ANY,
        )


class TestGff3ToFastaMain(unittest.TestCase):
    def test_main_exits_for_invalid_sequence_type(self):
        with self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="invalid",
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )
        self.assertEqual(exc.exception.code, 1)

    def test_main_exits_when_user_defined_missing_for_user_defined_type(self):
        with self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="user_defined",
                user_defined=None,
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )
        self.assertEqual(exc.exception.code, 1)

    def test_main_exits_when_user_defined_has_wrong_shape(self):
        with self.assertRaises(SystemExit) as exc:
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="user_defined",
                user_defined=["mRNA"],
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )
        self.assertEqual(exc.exception.code, 1)

    def test_main_routes_cds_to_splicer_and_writes_output(self):
        fake_gff = mock.Mock()
        output_handle = io.StringIO()

        with mock.patch.object(gff3_to_fasta, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(gff3_to_fasta, "splicer", autospec=True, return_value={">tx1": "ATG"}) as splicer_mock, \
            mock.patch("builtins.open", return_value=output_handle):
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="cds",
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )

        splicer_mock.assert_called_once_with(fake_gff, ["CDS"], "simple", "cds", False)
        self.assertIn(">tx1\nATG\n", output_handle.getvalue())

    def test_main_all_mode_calls_extract_and_splice_paths(self):
        fake_gff = mock.Mock()

        with mock.patch.object(gff3_to_fasta, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(gff3_to_fasta, "extract_start_end", autospec=True, return_value={">a": "A"}) as extract_mock, \
            mock.patch.object(gff3_to_fasta, "splicer", autospec=True, return_value={">b": "ATG"}) as splicer_mock, \
            mock.patch("builtins.open", return_value=io.StringIO()):
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="all",
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )

        self.assertEqual(extract_mock.call_count, 3)
        self.assertEqual(splicer_mock.call_count, 3)
        self.assertEqual(extract_mock.call_args_list[0].args[1], "pre_trans")
        self.assertEqual(extract_mock.call_args_list[1].args[1], "gene")
        self.assertEqual(extract_mock.call_args_list[2].args[1], "exon")
        self.assertEqual(splicer_mock.call_args_list[0].args[1], ["exon", "pseudogenic_exon"])
        self.assertEqual(splicer_mock.call_args_list[1].args[1], ["CDS"])
        self.assertEqual(splicer_mock.call_args_list[2].args[1], ["CDS"])


if __name__ == "__main__":
    unittest.main()