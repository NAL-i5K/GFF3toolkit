#!/usr/bin/env python3
"""CLI smoke tests with basic output assertions.

This script is used by CI and can also be run locally:
	python tests.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BIN_DIR = Path(sys.executable).parent


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


def run_command(name: str, args: list[str], expected_files: list[Path]) -> None:
	cmd_name = args[0]
	cmd_path = BIN_DIR / cmd_name
	if sys.platform.startswith("win"):
		cmd_path = cmd_path.with_suffix(".exe")
	cmd = [str(cmd_path), *args[1:]]

	print(f"[RUN] {name}: {' '.join(cmd)}")
	result = subprocess.run(cmd, cwd=ROOT)
	if result.returncode != 0:
		raise AssertionError(f"Command failed ({name}) with return code {result.returncode}")
	for output_path in expected_files:
		assert_non_empty(output_path)
	print(f"[PASS] {name}")


def main() -> int:
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
	except Exception as exc:  # noqa: BLE001
		print(f"[FAIL] {exc}", file=sys.stderr)
		return 1

	print("[PASS] CLI smoke test suite completed")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
