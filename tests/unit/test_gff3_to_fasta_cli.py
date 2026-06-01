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
            None,
        )

    def test_script_main_passes_defline_attributes(self):
        args = Namespace(
            gff="input.gff3",
            fasta="ref.fa",
            embedded_fasta=False,
            sequence_type="gene",
            user_defined=None,
            defline="custom",
            defline_attributes="product|ID",
            output_prefix="out",
            quality_control=False,
        )

        with mock.patch("argparse.ArgumentParser.parse_args", return_value=args), \
            mock.patch.object(gff3_to_fasta, "main", autospec=True) as main_mock:
            gff3_to_fasta.script_main()

        main_mock.assert_called_once_with(
            "input.gff3",
            "ref.fa",
            False,
            "gene",
            None,
            "custom",
            False,
            "out",
            mock.ANY,
            "product|ID",
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
        with mock.patch("builtins.open", return_value=io.StringIO()):
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
        with mock.patch("builtins.open", return_value=io.StringIO()):
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

    def test_main_exits_for_custom_defline_without_attributes(self):
        with mock.patch("builtins.open", return_value=io.StringIO()):
            with self.assertRaises(SystemExit) as exc:
                gff3_to_fasta.main(
                    gff_file="input.gff3",
                    fasta_file="ref.fa",
                    stype="gene",
                    dline="custom",
                    output_prefix="out",
                    qc=False,
                    logger=mock.Mock(),
                    defline_attributes=None,
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

        splicer_mock.assert_called_once_with(fake_gff, ["CDS"], "simple", "cds", False, [])
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

    def test_main_can_append_selected_attributes_to_defline(self):
        fake_gff = mock.Mock()
        output_handle = io.StringIO()

        with mock.patch.object(gff3_to_fasta, "Gff3", autospec=True, return_value=fake_gff), \
            mock.patch.object(gff3_to_fasta, "extract_start_end", autospec=True, return_value={">product=alcohol dehydrogenase|ID=OFAS1234": "ATG"}) as extract_mock, \
            mock.patch("builtins.open", return_value=output_handle):
            gff3_to_fasta.main(
                gff_file="input.gff3",
                fasta_file="ref.fa",
                stype="gene",
                dline="custom",
                defline_attributes="product|ID",
                output_prefix="out",
                qc=False,
                logger=mock.Mock(),
            )

        extract_mock.assert_called_once_with(fake_gff, "gene", "custom", False, ["product", "ID"])
        self.assertIn(">product=alcohol dehydrogenase|ID=OFAS1234\nATG\n", output_handle.getvalue())


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

    def test_normalize_defline_attributes_deduplicates_and_strips_assignments(self):
        normalized = gff3_to_fasta._normalize_defline_attributes(" product |ID=tx1|product||Dbxref=GeneID:1 ")
        self.assertEqual(normalized, ["product", "ID", "Dbxref"])

    def test_stringify_attribute_value_handles_nested_list_and_dict(self):
        value = {
            "Dbxref": ["GeneID:1", "HGNC:2"],
            "meta": {"source": "RefSeq"},
        }

        self.assertEqual(
            gff3_to_fasta._stringify_attribute_value(value),
            "Dbxref=GeneID:1,HGNC:2,meta=source=RefSeq",
        )

    def test_format_defline_attributes_supports_custom_and_append_modes(self):
        record = {"attributes": {"product": "alcohol dehydrogenase", "ID": "tx1"}}

        custom = gff3_to_fasta._format_defline_attributes(record, "product|ID", "custom")
        appended = gff3_to_fasta._format_defline_attributes(record, ["product", "ID"], "simple")

        self.assertEqual(custom, "product=alcohol dehydrogenase|ID=tx1")
        self.assertEqual(appended, "|product=alcohol dehydrogenase|ID=tx1")

    def test_extract_start_end_custom_defline_uses_requested_attributes(self):
        root_gene = {
            "line_type": "feature",
            "attributes": {
                "ID": "gene1",
                "Name": "gene1",
                "product": "dehydrogenase",
            },
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
        gff = _MiniGff(
            lines=[root_gene],
            fasta_external={"chr1": {"seq": "AAAACCCC"}},
        )

        gene_seq = gff3_to_fasta.extract_start_end(
            gff,
            "gene",
            "custom",
            embedded_fasta=False,
            defline_attributes="product|ID",
        )

        self.assertEqual(gene_seq, {">product=dehydrogenase|ID=gene1": "AAAA"})

    def test_splicer_custom_defline_for_cds_uses_mrna_attributes(self):
        cds = {
            "line_type": "feature",
            "attributes": {"ID": "cds1", "Parent": ["tx1"]},
            "line_index": 2,
            "line_raw": "cds",
            "type": "CDS",
            "seqid": "chr1",
            "start": 1,
            "end": 3,
            "strand": "+",
            "phase": 0,
            "children": [],
            "parents": [],
        }
        mrna = {
            "line_type": "feature",
            "attributes": {"ID": "tx1", "Parent": ["gene1"], "product": "enzyme"},
            "line_index": 1,
            "line_raw": "mrna",
            "type": "mRNA",
            "seqid": "chr1",
            "start": 1,
            "end": 3,
            "strand": "+",
            "phase": 0,
            "children": [cds],
            "parents": [],
        }
        root_gene = {
            "line_type": "feature",
            "attributes": {"ID": "gene1"},
            "line_index": 0,
            "line_raw": "gene",
            "type": "gene",
            "seqid": "chr1",
            "start": 1,
            "end": 3,
            "strand": "+",
            "children": [mrna],
            "parents": [],
        }
        gff = _MiniGff(
            lines=[root_gene, mrna, cds],
            fasta_external={"chr1": {"seq": "ATG"}},
        )

        seq = gff3_to_fasta.splicer(
            gff,
            ["CDS"],
            "custom",
            "cds",
            embedded_fasta=False,
            defline_attributes="product|ID",
        )

        self.assertEqual(seq, {">product=enzyme|ID=tx1": "ATG"})


if __name__ == "__main__":
    unittest.main()