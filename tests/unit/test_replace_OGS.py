import unittest
from collections import defaultdict

from gff3tool.lib import replace_OGS


class FakeGff:
    def __init__(self, lines):
        self.lines = lines
        self.features = defaultdict(list)
        self.removed = []
        for line in lines:
            line_id = line.get("attributes", {}).get("ID")
            if line_id:
                self.features[line_id].append(line)

    def collect_descendants(self, line):
        descendants = []
        for child in line.get("children", []):
            descendants.append(child)
            descendants.extend(self.collect_descendants(child))
        return descendants

    def collect_roots(self, line):
        if "roots" in line:
            return line["roots"]
        if "parents" in line and line["parents"]:
            return line["parents"][0]
        return [line]

    def remove(self, line):
        line["line_status"] = "removed"
        self.removed.append(line)


def make_feature(
    feature_id,
    feature_type,
    seqid="chr1",
    start=1,
    end=10,
    line_index=0,
    parent_ids=None,
    replace=None,
    name=None,
):
    attrs = {"ID": feature_id}
    if parent_ids:
        attrs["Parent"] = list(parent_ids)
    if replace is not None:
        attrs["replace"] = list(replace)
    if name is not None:
        attrs["Name"] = name

    return {
        "line_type": "feature",
        "line_raw": f"{feature_id}-raw",
        "line_index": line_index,
        "seqid": seqid,
        "start": start,
        "end": end,
        "strand": "+",
        "type": feature_type,
        "attributes": attrs,
        "children": [],
        "parents": [],
    }


class TestReplaceOGSFeatureSort(unittest.TestCase):
    def test_feature_sort_orders_by_seq_start_and_feature_priority(self):
        gene_chr2 = make_feature("gene2", "gene", seqid="chr2", start=5, end=50)
        exon_chr1 = make_feature("tx1-exon", "exon", seqid="chr1", start=10, end=20)
        cds_chr1 = make_feature("tx1-cds", "CDS", seqid="chr1", start=10, end=18)
        mrna_chr1 = make_feature("tx1", "mRNA", seqid="chr1", start=10, end=30)

        ordered = replace_OGS.featureSort([gene_chr2, exon_chr1, cds_chr1, mrna_chr1])

        self.assertEqual(
            [item["attributes"]["ID"] for item in ordered],
            ["tx1", "tx1-exon", "tx1-cds", "gene2"],
        )

    def test_feature_sort_reverse_uses_end_coordinate_then_reverse_priority(self):
        exon = make_feature("tx1-exon", "exon", seqid="chr1", start=10, end=30)
        cds = make_feature("tx1-cds", "CDS", seqid="chr1", start=15, end=30)

        ordered = replace_OGS.featureSort([exon, cds], reverse=True)

        self.assertEqual([item["attributes"]["ID"] for item in ordered], ["tx1-exon", "tx1-cds"])

    def test_feature_sort_raises_for_non_numeric_seqid_suffix(self):
        gene = make_feature("geneA", "gene", seqid="chrX", start=1, end=10)

        with self.assertRaises(AttributeError):
            replace_OGS.featureSort([gene])


class TestReplaceOGSGroups(unittest.TestCase):
    def test_replace_id_name_normalizes_brackets_without_forcing_name_rewrite(self):
        groups = replace_OGS.Groups(outsideNum=0)
        line = make_feature("LOC0001", "gene", name="LOC0001[alpha]")

        groups.replaceIDName(line, "LOC0002")

        self.assertEqual(line["attributes"]["ID"], "LOC0002")
        self.assertEqual(line["attributes"]["Name"], "LOC0001(alpha)")

    def test_replace_id_name_updates_name_when_name_matches_id(self):
        groups = replace_OGS.Groups(outsideNum=0)
        line = make_feature("LOC0001", "gene", name="LOC0001")

        groups.replaceIDName(line, "LOC0002")

        self.assertEqual(line["attributes"]["ID"], "LOC0002")
        self.assertEqual(line["attributes"]["Name"], "LOC0002")

    def test_replace_id_name_only_updates_id_when_name_not_in_id(self):
        groups = replace_OGS.Groups(outsideNum=0)
        line = make_feature("LOC0001", "gene", name="descriptive-name")

        groups.replaceIDName(line, "LOC0002")

        self.assertEqual(line["attributes"]["ID"], "LOC0002")
        self.assertEqual(line["attributes"]["Name"], "descriptive-name")

    def test_name2id_populates_name_and_id_mappings(self):
        root = make_feature("LOC0001", "gene", line_index=0, name="GeneA")
        child = make_feature(
            "LOC0001-RA",
            "mRNA",
            line_index=1,
            parent_ids=["LOC0001"],
            name="TranscriptA",
        )
        exon = make_feature(
            "LOC0001-RA-exon",
            "exon",
            line_index=2,
            parent_ids=["LOC0001-RA"],
            name="ExonA",
        )
        child["children"].append(exon)
        root["children"].append(child)
        child["parents"] = [[root]]
        exon["parents"] = [[child]]

        mgff = FakeGff([root, child, exon])
        groups = replace_OGS.Groups(outsideNum=0)

        groups.name2id(mgff)

        self.assertEqual(groups.mapName2ID["TranscriptA"], "LOC0001-RA")
        self.assertEqual(groups.mapName2ID["LOC0001-RA"], "LOC0001-RA")
        self.assertEqual(groups.id2name["LOC0001"], "GeneA")
        self.assertEqual(groups.id2name["LOC0001-RA"], "TranscriptA")
        self.assertEqual(groups.idprefix, "LOC")

    def test_grouping_marks_add_when_only_na_replace_present(self):
        root = make_feature("LOC0001", "gene", line_index=0)
        child = make_feature(
            "LOC0001-RA",
            "mRNA",
            line_index=1,
            parent_ids=["LOC0001"],
            replace=["NA"],
        )
        root["children"].append(child)
        child["parents"] = [[root]]
        wgff = FakeGff([root, child])

        replace_OGS.Groups(WAgff=wgff, outsideNum=0)

        self.assertEqual(child["attributes"]["replace_type"], "add")
        self.assertEqual(root["attributes"]["replace_type"], "add")

    def test_grouping_marks_split_when_same_replace_used_by_distinct_parents(self):
        root1 = make_feature("LOC0001", "gene", line_index=0)
        child1 = make_feature(
            "LOC0001-RA",
            "mRNA",
            line_index=1,
            parent_ids=["LOC0001"],
            replace=["REF1"],
        )
        root1["children"].append(child1)
        child1["parents"] = [[root1]]

        root2 = make_feature("LOC0002", "gene", line_index=2)
        child2 = make_feature(
            "LOC0002-RA",
            "mRNA",
            line_index=3,
            parent_ids=["LOC0002"],
            replace=["REF1"],
        )
        root2["children"].append(child2)
        child2["parents"] = [[root2]]

        wgff = FakeGff([root1, child1, root2, child2])

        replace_OGS.Groups(WAgff=wgff, outsideNum=0)

        self.assertEqual(child1["attributes"]["replace_type"], "split")
        self.assertEqual(child2["attributes"]["replace_type"], "split")
        self.assertEqual(root1["attributes"]["replace_type"], "split")
        self.assertEqual(root2["attributes"]["replace_type"], "split")

    def test_rename_id_uses_ascii_suffixes_for_multiple_transcripts(self):
        root = make_feature("LOC0001", "gene", line_index=0, name="LOC0001")

        child_a = make_feature(
            "LOC0001-RA",
            "mRNA",
            line_index=1,
            parent_ids=["LOC0001"],
            name="LOC0001-RA",
        )
        exon_a = make_feature(
            "LOC0001-RA-EXON",
            "exon",
            line_index=2,
            parent_ids=["LOC0001-RA"],
            name="LOC0001-RA-EXON",
        )
        cds_a = make_feature(
            "LOC0001-RA-CDS",
            "CDS",
            line_index=3,
            parent_ids=["LOC0001-RA"],
            name="LOC0001-RA-CDS",
        )
        child_a["children"] = [exon_a, cds_a]
        exon_a["parents"] = [[child_a]]
        cds_a["parents"] = [[child_a]]

        child_b = make_feature(
            "LOC0001-RB",
            "mRNA",
            line_index=4,
            parent_ids=["LOC0001"],
            name="LOC0001-RB",
        )
        child_b["children"] = []

        root["children"] = [child_a, child_b]
        child_a["parents"] = [[root]]
        child_b["parents"] = [[root]]

        wgff = FakeGff([root, child_a, exon_a, cds_a, child_b])
        groups = replace_OGS.Groups(outsideNum=0)
        groups.WAgff = wgff

        groups.renameID(root, "LOC9000")

        self.assertEqual(root["attributes"]["ID"], "LOC9000")
        self.assertEqual(child_a["attributes"]["ID"], "LOC9000-RA")
        self.assertEqual(child_b["attributes"]["ID"], "LOC9000-RB")
        self.assertEqual(child_a["attributes"]["Parent"], ["LOC9000"])
        self.assertEqual(child_b["attributes"]["Parent"], ["LOC9000"])
        self.assertEqual(exon_a["attributes"]["ID"], "LOC9000-RA-EXON01")
        self.assertEqual(exon_a["attributes"]["Parent"], ["LOC9000-RA"])
        self.assertEqual(cds_a["attributes"]["ID"], "LOC9000-RA-CDS")
        self.assertEqual(cds_a["attributes"]["Parent"], ["LOC9000-RA"])

    def test_rename_id_returns_warning_for_non_dict_input(self):
        groups = replace_OGS.Groups(outsideNum=0)

        warning = groups.renameID(["not", "a", "dict"], "LOC9000")

        self.assertIn("The line is not a dict structure", warning)


class TestReplaceOGSUTRAndReplacer(unittest.TestCase):
    def test_new_utr_feature_links_to_parent_and_features_table(self):
        parent = make_feature("LOC0001-RA", "mRNA", line_index=0)
        exon = make_feature(
            "LOC0001-RA-EXON01",
            "exon",
            line_index=1,
            parent_ids=["LOC0001-RA"],
        )
        exon["parents"] = [[parent]]
        parent["children"] = [exon]
        gff = FakeGff([parent, exon])
        groups = replace_OGS.Groups(outsideNum=0)

        newf = groups.newUTRfeature("five_prime_utr", exon, "LOC0001-RA", gff)

        self.assertEqual(newf["type"], "five_prime_utr")
        self.assertEqual(newf["attributes"]["ID"], "LOC0001-RA-five_prime_utr")
        self.assertEqual(newf["attributes"]["Parent"], ["LOC0001-RA"])
        self.assertIn(newf, gff.lines)
        self.assertIn(newf, gff.features[newf["attributes"]["ID"]])
        self.assertIn(newf, parent["children"])

    def test_gen5utr_creates_full_and_partial_features(self):
        parent = make_feature("LOC0001-RA", "mRNA", line_index=0)
        exon_full = make_feature("ex1", "exon", start=50, end=90, line_index=1, parent_ids=["LOC0001-RA"])
        exon_partial = make_feature("ex2", "exon", start=95, end=130, line_index=2, parent_ids=["LOC0001-RA"])
        for exon in (exon_full, exon_partial):
            exon["parents"] = [[parent]]
        parent["children"] = [exon_full, exon_partial]
        cds = make_feature("cds", "CDS", start=100, end=180, line_index=3, parent_ids=["LOC0001-RA"])
        gff = FakeGff([parent, exon_full, exon_partial, cds])
        groups = replace_OGS.Groups(outsideNum=0)

        groups.gen5UTR("five_prime_utr", cds, [exon_full, exon_partial], "LOC0001-RA", gff)

        utrs = [l for l in gff.lines if l.get("type") == "five_prime_utr"]
        self.assertEqual(len(utrs), 2)
        self.assertTrue(any(u["start"] == 50 and u["end"] == 90 for u in utrs))
        self.assertTrue(any(u["start"] == 95 and u["end"] == 99 for u in utrs))

    def test_gen3utr_creates_full_and_partial_features(self):
        parent = make_feature("LOC0001-RA", "mRNA", line_index=0)
        exon_partial = make_feature("ex1", "exon", start=140, end=170, line_index=1, parent_ids=["LOC0001-RA"])
        exon_full = make_feature("ex2", "exon", start=190, end=220, line_index=2, parent_ids=["LOC0001-RA"])
        for exon in (exon_partial, exon_full):
            exon["parents"] = [[parent]]
        parent["children"] = [exon_partial, exon_full]
        cds = make_feature("cds", "CDS", start=100, end=150, line_index=3, parent_ids=["LOC0001-RA"])
        gff = FakeGff([parent, exon_partial, exon_full, cds])
        groups = replace_OGS.Groups(outsideNum=0)

        groups.gen3UTR("three_prime_utr", cds, [exon_partial, exon_full], "LOC0001-RA", gff)

        utrs = [l for l in gff.lines if l.get("type") == "three_prime_utr"]
        self.assertEqual(len(utrs), 2)
        self.assertTrue(any(u["start"] == 151 and u["end"] == 170 for u in utrs))
        self.assertTrue(any(u["start"] == 190 and u["end"] == 220 for u in utrs))

    def test_replacer_add_delete_single_child_calls_remove(self):
        groups = replace_OGS.Groups(outsideNum=0)
        rg = replace_OGS.Groups(outsideNum=0)
        line = make_feature("WA1", "gene", line_index=0, replace=["NA"])
        line["attributes"]["replace_type"] = "add"

        deleted_child = make_feature(
            "WA1-RA",
            "mRNA",
            line_index=1,
            parent_ids=["WA1"],
        )
        deleted_child["attributes"]["status"] = "Delete"
        newtarget = make_feature("NEW1", "gene", line_index=2)
        newtarget["children"] = [deleted_child]
        mgff = FakeGff([newtarget, deleted_child])
        mgff.features["NEW1"] = [newtarget]

        groups.replacer_add = lambda _line, _rg, _mgff: {"ID": "NEW1", "maxnum": 1}

        groups.replacer(line, rg, mgff)

        self.assertEqual(len(mgff.removed), 1)
        self.assertIs(mgff.removed[0], deleted_child)

    def test_replacer_add_delete_one_of_many_marks_removed(self):
        groups = replace_OGS.Groups(outsideNum=0)
        rg = replace_OGS.Groups(outsideNum=0)
        line = make_feature("WA1", "gene", line_index=0, replace=["NA"])
        line["attributes"]["replace_type"] = "add"

        deleted_child = make_feature(
            "WA1-RA",
            "mRNA",
            line_index=1,
            parent_ids=["WA1"],
        )
        deleted_child["attributes"]["status"] = "delete"
        keep_child = make_feature(
            "WA1-RB",
            "mRNA",
            line_index=2,
            parent_ids=["WA1"],
        )
        newtarget = make_feature("NEW1", "gene", line_index=3)
        newtarget["children"] = [deleted_child, keep_child]
        mgff = FakeGff([newtarget, deleted_child, keep_child])
        mgff.features["NEW1"] = [newtarget]

        groups.replacer_add = lambda _line, _rg, _mgff: {"ID": "NEW1", "maxnum": 1}

        groups.replacer(line, rg, mgff)

        self.assertEqual(mgff.removed, [])
        self.assertEqual(deleted_child["line_status"], "removed")

    def test_grouping_user_defined_promotes_na_to_specific_replace_tag(self):
        root = make_feature("LOC0001", "gene", line_index=0)
        child_na = make_feature(
            "LOC0001-RA",
            "mRNA",
            line_index=1,
            parent_ids=["LOC0001"],
            replace=["NA"],
        )
        child_ref = make_feature(
            "LOC0001-RB",
            "mRNA",
            line_index=2,
            parent_ids=["LOC0001"],
            replace=["REF1"],
        )
        root["children"] = [child_na, child_ref]
        child_na["parents"] = [[root]]
        child_ref["parents"] = [[root]]
        wgff = FakeGff([root, child_na, child_ref])

        replace_OGS.Groups(WAgff=wgff, outsideNum=0, user_defined1=[["mRNA"]])

        self.assertEqual(child_na["attributes"]["replace"], ["REF1"])
        self.assertEqual(child_na["attributes"]["replace_type"], "simple")
        self.assertEqual(root["attributes"]["replace_type"], "simple")

    def test_grouping_marks_internal_review_when_children_have_mixed_types(self):
        root = make_feature("LOC0001", "gene", line_index=0)
        child_na = make_feature(
            "LOC0001-RA",
            "mRNA",
            line_index=1,
            parent_ids=["LOC0001"],
            replace=["NA"],
        )
        child_ref1 = make_feature(
            "LOC0001-RB",
            "mRNA",
            line_index=2,
            parent_ids=["LOC0001"],
            replace=["REF1"],
        )
        child_ref2 = make_feature(
            "LOC0001-RC",
            "mRNA",
            line_index=3,
            parent_ids=["LOC0001"],
            replace=["REF2"],
        )
        root["children"] = [child_na, child_ref1, child_ref2]
        child_na["parents"] = [[root]]
        child_ref1["parents"] = [[root]]
        child_ref2["parents"] = [[root]]
        wgff = FakeGff([root, child_na, child_ref1, child_ref2])

        replace_OGS.Groups(WAgff=wgff, outsideNum=0)

        self.assertIn("manual", child_na["attributes"]["replace_type"])
        self.assertEqual(root["attributes"]["replace_type"], "internal_review")

    def test_replacer_non_add_removes_target_with_single_isoform_parent(self):
        groups = replace_OGS.Groups(outsideNum=0)
        rg = replace_OGS.Groups(outsideNum=0)
        rg.mapName2ID = {"REF1": "tx1"}
        line = make_feature("WA1", "gene", line_index=0, replace=["REF1"])
        line["attributes"]["replace_type"] = "simple"

        parent = make_feature("GENE1", "gene", line_index=1)
        target = make_feature("tx1", "mRNA", line_index=2, parent_ids=["GENE1"])
        target["parents"] = [[parent]]
        parent["children"] = [target]
        newtarget = make_feature("NEW1", "gene", line_index=3)

        mgff = FakeGff([parent, target, newtarget])
        mgff.features["tx1"] = [target]
        mgff.features["NEW1"] = [newtarget]
        groups.replacer_add = lambda _line, _rg, _mgff: {"ID": "NEW1", "maxnum": 1}

        groups.replacer(line, rg, mgff)

        self.assertEqual([ld["attributes"]["ID"] for ld in mgff.removed], ["tx1"])
        self.assertIn("modified_track", newtarget["attributes"])

    def test_replacer_multi_ref_updates_tags_and_marks_reference_models_removed(self):
        groups = replace_OGS.Groups(outsideNum=0)
        rg = replace_OGS.Groups(outsideNum=0)
        rg.mapName2ID = {"REF1": "tx1"}
        line = make_feature("WA1", "gene", line_index=0, replace=["REF1"])
        line["attributes"]["replace_type"] = "multi-ref"

        wa_tx = make_feature("WA1-RA", "mRNA", line_index=1, parent_ids=["WA1"])
        line["children"] = [wa_tx]

        parent = make_feature("GENE1", "gene", line_index=2)
        ref_tx = make_feature("tx1", "mRNA", line_index=3, parent_ids=["GENE1"], name="REF1")
        extra_tx = make_feature("tx_extra", "mRNA", line_index=4, parent_ids=["GENE1"], name="REF_EXTRA")
        ref_desc = make_feature("tx1-ex1", "exon", line_index=5, parent_ids=["tx1"])
        ref_tx["children"] = [ref_desc]
        parent["children"] = [ref_tx, extra_tx]
        ref_tx["parents"] = [[parent]]
        extra_tx["parents"] = [[parent]]
        ref_desc["parents"] = [[ref_tx]]

        newtarget = make_feature("NEW1", "gene", line_index=6, replace=["REF1"])

        mgff = FakeGff([parent, ref_tx, extra_tx, ref_desc, newtarget])
        mgff.features["tx1"] = [ref_tx]
        mgff.features["GENE1"] = [parent]
        mgff.features["NEW1"] = [newtarget]
        groups.replacer_add = lambda _line, _rg, _mgff: {"ID": "NEW1", "maxnum": 1}

        msg = groups.replacer_multi(line, rg, mgff)

        self.assertIn("Add WA1 as NEW1", msg)
        self.assertEqual(ref_tx["line_status"], "removed")
        self.assertEqual(ref_desc["line_status"], "removed")
        self.assertEqual(extra_tx["line_status"], "removed")
        self.assertIn("REF_EXTRA", line["attributes"]["replace"])



if __name__ == "__main__":
    unittest.main()
