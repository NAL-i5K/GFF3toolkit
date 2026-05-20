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
        with mock.patch("builtins.open", return_value=io.StringIO()) as open_mock:
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

        open_mock.assert_not_called()
        self.assertEqual(exc.exception.code, 1)

    def test_main_exits_when_user_defined_has_wrong_shape(self):
        with mock.patch("builtins.open", return_value=io.StringIO()) as open_mock:
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

        open_mock.assert_not_called()
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

    def test_main_pep_translates_and_rewrites_header_tag(self):
        fake_gff = mock.Mock()
        output_handle = io.StringIO()

        with mock.patch.object(gff3_to_fasta, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(
                gff3_to_fasta,
                "splicer",
                autospec=True,
                return_value={">tx1|mRNA(CDS)|": "ATGGCC"},
            ), \
            mock.patch("builtins.open", return_value=output_handle):
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="pep",
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )

        self.assertIn(">tx1|peptide|\nMA\n", output_handle.getvalue())

    def test_main_user_defined_writes_output_when_parent_child_are_provided(self):
        fake_gff = mock.Mock()
        output_handle = io.StringIO()

        with mock.patch.object(gff3_to_fasta, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(
                gff3_to_fasta,
                "splicer",
                autospec=True,
                return_value={">u1": "ATGC"},
            ) as splicer_mock, \
            mock.patch("builtins.open", return_value=output_handle):
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="user_defined",
                user_defined=["mRNA", "CDS"],
                dline="simple",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )

        splicer_mock.assert_called_once_with(fake_gff, ["mRNA", "CDS"], "simple", "user_defined", False)
        self.assertIn(">u1\nATGC\n", output_handle.getvalue())


class _MiniGff:
    def __init__(self, lines, fasta_external=None, fasta_embedded=None):
        self.lines = lines
        self.fasta_external = fasta_external or {}
        self.fasta_embedded = fasta_embedded or {}


class TestGff3ToFastaHelpers(unittest.TestCase):
    def test_complement_and_translator_handle_expected_inputs(self):
        self.assertEqual(gff3_to_fasta.complement("ATGC"), "TACG")
        self.assertEqual(gff3_to_fasta.translator("AUGGCCUAA"), "MA*")
        self.assertEqual(gff3_to_fasta.translator("NNNXXX"), "X")

    def test_get_subseq_reads_external_and_reverse_complements(self):
        gff = _MiniGff(
            lines=[],
            fasta_external={"chr1": {"seq": "AACCGGTT"}},
            fasta_embedded={"chr1": {"seq": "TTTTTTTT"}},
        )
        line = {
            "seqid": "chr1",
            "start": 2,
            "end": 5,
            "strand": "-",
            "type": "exon",
            "line_index": 0,
            "line_raw": "x",
        }

        seq = gff3_to_fasta.get_subseq(gff, line, embedded_fasta=False)
        self.assertEqual(seq, "CGGT")

    def test_get_subseq_can_read_embedded_fasta(self):
        gff = _MiniGff(
            lines=[],
            fasta_external={"chr1": {"seq": "AAAAAAAA"}},
            fasta_embedded={"chr1": {"seq": "AACCGGTT"}},
        )
        line = {
            "seqid": "chr1",
            "start": 1,
            "end": 4,
            "strand": "+",
            "type": "gene",
            "line_index": 0,
            "line_raw": "x",
        }

        seq = gff3_to_fasta.get_subseq(gff, line, embedded_fasta=True)
        self.assertEqual(seq, "AACC")

    def test_extract_start_end_for_gene_and_exon_types(self):
        parent = {"attributes": {"ID": "tx1"}}
        root_gene = {
            "line_type": "feature",
            "attributes": {"ID": "gene1", "Name": "gene1"},
            "line_index": 0,
            "line_raw": "gene",
            "type": "gene",
            "seqid": "chr1",
            "start": 1,
            "end": 4,
            "strand": "+",
            "children": [],
            "parents": [],
        }
        exon = {
            "line_type": "feature",
            "attributes": {"ID": "ex1", "Name": "ex1"},
            "line_index": 1,
            "line_raw": "exon",
            "type": "exon",
            "seqid": "chr1",
            "start": 5,
            "end": 8,
            "strand": "+",
            "children": [],
            "parents": [[parent]],
        }
        gff = _MiniGff(
            lines=[root_gene, exon],
            fasta_external={"chr1": {"seq": "AAAACCCC"}},
        )

        gene_seq = gff3_to_fasta.extract_start_end(gff, "gene", "simple", embedded_fasta=False)
        exon_seq = gff3_to_fasta.extract_start_end(gff, "exon", "simple", embedded_fasta=False)

        self.assertEqual(gene_seq, {">gene1": "AAAA"})
        self.assertEqual(exon_seq, {">ex1": "CCCC"})

    def test_extract_start_end_pre_trans_uses_transcript_span(self):
        root = {
            "line_type": "feature",
            "attributes": {"ID": "gene1"},
            "line_index": 0,
            "line_raw": "gene",
            "type": "gene",
            "seqid": "chr1",
            "start": 1,
            "end": 8,
            "strand": "+",
            "parents": [],
            "children": [],
        }
        trans = {
            "line_type": "feature",
            "attributes": {"ID": "tx1", "Name": "tx1"},
            "line_index": 1,
            "line_raw": "mrna",
            "type": "mRNA",
            "seqid": "chr1",
            "start": 2,
            "end": 6,
            "strand": "+",
            "parents": [[root]],
            "children": [],
        }
        root["children"] = [trans]
        gff = _MiniGff(lines=[root, trans], fasta_external={"chr1": {"seq": "AACCGGTT"}})

        seq = gff3_to_fasta.extract_start_end(gff, "pre_trans", "simple", embedded_fasta=False)

        self.assertEqual(seq, {">tx1": "ACCGG"})

    def test_extract_start_end_user_defined_complete_includes_parent_field(self):
        parent = {"attributes": {"ID": "tx1"}}
        feature = {
            "line_type": "feature",
            "attributes": {"ID": "ud1", "Name": "ud1"},
            "line_index": 0,
            "line_raw": "ud",
            "type": "custom_feature",
            "seqid": "chr1",
            "start": 3,
            "end": 6,
            "strand": "+",
            "parents": [[parent]],
            "children": [],
        }
        gff = _MiniGff(lines=[feature], fasta_external={"chr1": {"seq": "AACCGGTT"}})

        seq = gff3_to_fasta.extract_start_end(gff, "custom_feature", "complete", embedded_fasta=False)

        self.assertEqual(len(seq), 1)
        defline = next(iter(seq.keys()))
        self.assertIn("Parent=tx1", defline)
        self.assertEqual(seq[defline], "CCGG")


if __name__ == "__main__":
    unittest.main()