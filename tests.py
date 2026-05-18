#!/usr/bin/env python3
"""CLI smoke tests with basic output assertions.

This script is used by CI and can also be run locally:
	python tests.py
"""

from __future__ import annotations

import subprocess
import sys
import shutil
import sysconfig
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON_DIR = Path(sys.executable).parent


def assert_blast_available() -> None:
	blast_roots = [ROOT / "gff3tool" / "lib" / "ncbi-blast+" / "bin"]
	purelib = Path(sysconfig.get_paths().get("purelib", ""))
	if purelib:
		blast_roots.append(purelib / "gff3tool" / "lib" / "ncbi-blast+" / "bin")

	binary_variants = [
		("makeblastdb", "makeblastdb.exe"),
		("blastn", "blastn.exe"),
	]

	missing_labels: list[str] = []
	for variants in binary_variants:
		found = False
		for root in blast_roots:
			if any((root / name).exists() for name in variants):
				found = True
				break
		if not found:
			missing_labels.append("/".join(variants))

	if missing_labels:
		paths_str = ", ".join(str(path) for path in blast_roots)
		bins_str = ", ".join(missing_labels)
		raise AssertionError(
			"Missing bundled BLAST executables required by gff3_QC smoke test: "
			f"{bins_str}. Looked in: {paths_str}. "
			"Install with `python -m pip install .` before running tests.py."
		)


def resolve_command(cmd_name: str) -> str:
	if sys.platform.startswith("win"):
		candidates = [
			PYTHON_DIR / "Scripts" / f"{cmd_name}.exe",
			PYTHON_DIR / f"{cmd_name}.exe",
		]
	else:
		candidates = [PYTHON_DIR / cmd_name]

	for candidate in candidates:
		if candidate.exists():
			return str(candidate)

	from_path = shutil.which(cmd_name)
	if from_path:
		return from_path

	return str(candidates[0])


def remove_if_exists(path: Path) -> None:
	if path.exists():
		if path.is_file():
			path.unlink()
		else:
			for child in path.glob("*"):
				if child.is_file():
					child.unlink()
			path.rmdir()


def assert_non_empty(path: Path) -> None:
	if not path.exists():
		raise AssertionError(f"Expected output file was not created: {path}")
	if path.stat().st_size == 0:
		raise AssertionError(f"Output file is empty: {path}")


def assert_file_contains(path: Path, snippet: str) -> None:
	content = path.read_text(encoding="utf-8", errors="replace")
	if snippet not in content:
		raise AssertionError(f"Expected '{snippet}' in {path}, but it was not found")


def assert_file_contains_any(path: Path, snippets: list[str]) -> None:
	content = path.read_text(encoding="utf-8", errors="replace")
	if not any(snippet in content for snippet in snippets):
		joined = ", ".join(repr(snippet) for snippet in snippets)
		raise AssertionError(f"Expected one of {joined} in {path}, but none were found")


def assert_fasta_has_header(path: Path) -> None:
	content = path.read_text(encoding="utf-8", errors="replace")
	if not any(line.startswith(">") for line in content.splitlines()):
		raise AssertionError(f"Expected at least one FASTA header in {path}")


def run_command(name: str, args: list[str], expected_files: list[Path]) -> None:
	cmd = [resolve_command(args[0]), *args[1:]]
	for output_path in expected_files:
		remove_if_exists(output_path)

	print(f"[RUN] {name}: {' '.join(cmd)}")
	result = subprocess.run(cmd, cwd=ROOT)
	if result.returncode != 0:
		raise AssertionError(f"Command failed ({name}) with return code {result.returncode}")
	for output_path in expected_files:
		assert_non_empty(output_path)
	print(f"[PASS] {name}")


def main() -> int:
	assert_blast_available()

	# Clean outputs that this script validates.
	for path in [
		ROOT / "error.txt",
		ROOT / "corrected.gff3",
		ROOT / "merged.gff",
		ROOT / "merged_report.txt",
		ROOT / "example-sorted.gff3",
		ROOT / "test_sequences_pre_trans.fa",
		ROOT / "test_sequences_gene.fa",
		ROOT / "test_sequences_exon.fa",
		ROOT / "test_sequences_trans.fa",
		ROOT / "test_sequences_cds.fa",
		ROOT / "test_sequences_pep.fa",
	]:
		remove_if_exists(path)

	checks: list[tuple[str, list[str], list[Path]]] = [
		(
			"gff3_QC",
			[
				"gff3_QC",
				"-g",
				"example_file/example.gff3",
				"-f",
				"example_file/reference.fa",
				"-o",
				"error.txt",
			],
			[ROOT / "error.txt"],
		),
		(
			"gff3_fix",
			[
				"gff3_fix",
				"-qc_r",
				"error.txt",
				"-g",
				"example_file/example.gff3",
				"-og",
				"corrected.gff3",
			],
			[ROOT / "corrected.gff3"],
		),
		(
			"gff3_merge default",
			[
				"gff3_merge",
				"-g1",
				"example_file/new_models.gff3",
				"-g2",
				"example_file/reference.gff3",
				"-f",
				"example_file/reference.fa",
				"-og",
				"merged.gff",
				"-r",
				"merged_report.txt",
			],
			[ROOT / "merged.gff", ROOT / "merged_report.txt"],
		),
		(
			"gff3_merge u1+u2",
			[
				"gff3_merge",
				"-g1",
				"example_file/new_models.gff3",
				"-g2",
				"example_file/reference.gff3",
				"-f",
				"example_file/reference.fa",
				"-og",
				"merged.gff",
				"-u1",
				"example_file/u1.txt",
				"-u2",
				"example_file/u2.txt",
				"-r",
				"merged_report.txt",
			],
			[ROOT / "merged.gff", ROOT / "merged_report.txt"],
		),
		(
			"gff3_merge u1",
			[
				"gff3_merge",
				"-g1",
				"example_file/new_models.gff3",
				"-g2",
				"example_file/reference.gff3",
				"-f",
				"example_file/reference.fa",
				"-og",
				"merged.gff",
				"-u1",
				"example_file/u1.txt",
				"-r",
				"merged_report.txt",
			],
			[ROOT / "merged.gff", ROOT / "merged_report.txt"],
		),
		(
			"gff3_merge u2",
			[
				"gff3_merge",
				"-g1",
				"example_file/new_models.gff3",
				"-g2",
				"example_file/reference.gff3",
				"-f",
				"example_file/reference.fa",
				"-og",
				"merged.gff",
				"-u2",
				"example_file/u2.txt",
				"-r",
				"merged_report.txt",
			],
			[ROOT / "merged.gff", ROOT / "merged_report.txt"],
		),
		(
			"gff3_merge noAuto",
			[
				"gff3_merge",
				"-g1",
				"example_file/new_models_w_replace.gff3",
				"-g2",
				"example_file/reference.gff3",
				"-f",
				"example_file/reference.fa",
				"-og",
				"merged.gff",
				"-r",
				"merged_report.txt",
				"-noAuto",
			],
			[ROOT / "merged.gff", ROOT / "merged_report.txt"],
		),
		(
			"gff3_sort",
			["gff3_sort", "-g", "example_file/example.gff3", "-og", "example-sorted.gff3"],
			[ROOT / "example-sorted.gff3"],
		),
		(
			"gff3_to_fasta",
			[
				"gff3_to_fasta",
				"-g",
				"example_file/example.gff3",
				"-f",
				"example_file/reference.fa",
				"-st",
				"all",
				"-d",
				"simple",
				"-o",
				"test_sequences",
			],
			[
				ROOT / "test_sequences_pre_trans.fa",
				ROOT / "test_sequences_gene.fa",
				ROOT / "test_sequences_exon.fa",
				ROOT / "test_sequences_trans.fa",
				ROOT / "test_sequences_cds.fa",
				ROOT / "test_sequences_pep.fa",
			],
		),
	]

	try:
		for name, args, expected_files in checks:
			run_command(name, args, expected_files)
			if name == "gff3_QC":
				assert_file_contains_any(ROOT / "error.txt", ["Line ", "Error", "Ema", "Esf"])
			elif name == "gff3_merge default":
				assert_file_contains(ROOT / "merged_report.txt", "# Number of WA loci")
				assert_file_contains(ROOT / "merged_report.txt", "Change_log")
			elif name == "gff3_to_fasta":
				for fasta_path in expected_files:
					assert_fasta_has_header(fasta_path)
	except Exception as exc:  # noqa: BLE001
		print(f"[FAIL] {exc}", file=sys.stderr)
		return 1

	print("[PASS] CLI smoke test suite completed")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
