import unittest
from collections import defaultdict

from gff3tool.lib import replace_OGS


class FakeGff:
    def __init__(self, lines):
        self.lines = lines
        self.features = defaultdict(list)
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


if __name__ == "__main__":
    unittest.main()
