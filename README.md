# GFF3toolkit - Python programs for processing GFF3 files

![example workflow](https://github.com/NAL-i5K/GFF3toolkit/actions/workflows/build.yml/badge.svg)
[![Build status](https://ci.appveyor.com/api/projects/status/0do5uwu5je0gag1u/branch/master?svg=true)](https://ci.appveyor.com/project/hsiaoyi0504/gff3toolkit/branch/master)
[![PyPI version](https://badge.fury.io/py/gff3tool.svg)](https://badge.fury.io/py/gff3tool)
[![Documentation Status](https://readthedocs.org/projects/gff3toolkit/badge/?version=latest)](https://gff3toolkit.readthedocs.io/en/latest/?badge=latest)

## Background

The [GFF3 format](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md) (Generic Feature Format Version 3) is one of the standard formats to describe and represent genomic features. It is an incredibly flexible, 9-column format, which is easily manipulated by biologists. This flexibility, however, makes it very easy to break the format. We have developed the GFF3toolkit to help identify common problems with GFF3 files; fix 30 of these common problems; sort GFF3 files (which can aid in using down-stream processing programs and custom parsing); merge two GFF3 files into a single, non-redundant GFF3 file; and generate FASTA files from a GFF3 file for many use cases (e.g. feature types beyond mRNA).

[Frequently Asked Questions/FAQ](docs/FAQ.md)

## Prerequisite

* Python 3.x
  * [wheel](https://pythonwheels.com/) (should have been installed for most python distributions, if you don't have, use `pip install wheel` to install it.)
* Perl

## Installation

### Stable release on PyPI

`pip install gff3tool`

### Latest version

`pip install git+https://github.com/NAL-i5K/GFF3toolkit.git`

## Current Functions

* [Detect GFF3 format errors](#detect-gff3-format-errors-back)
* [Correct GFF3 format errors](#correct-gff3-format-errors-back)
* [Merge two GFF3 files](#merge-two-gff3-files-back)
* [Sort a GFF3 file](#sort-a-gff3-file-back)
* [Generate biological sequences from a GFF3 file](#generate-biological-sequences-from-a-gff3-file-back)

## Usage

### Detect GFF3 format errors ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* `gff3_QC` - Detection of GFF format errors (~50 types of errors).
  * [gff3_QC readme](docs/gff3_QC.md)
  * [gff3_QC full documentation](docs/Detection-of-GFF3-format-errors.rst)
  * Quick start:
    `gff3_QC -g example_file/example.gff3 -f example_file/reference.fa -o error.txt -s statistic.txt`
  * Please refer to [gff3tool/lib/ERROR/ERROR.py](gff3tool/lib/ERROR/ERROR.py) to see the full list of Error codes and the corresponding Error tags.

### Correct GFF3 format errors ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* `gff3_fix` - Correct GFF3 errors detected by gff3_QC.py (30 types of errors).
  * [gff3_fix readme](docs/gff3_fix.md)
  * [gff3_fix full documentation](docs/gff3_fix.py-documentation.rst)
  * Quick start:
    `gff3_fix -qc_r error.txt -g example_file/example.gff3 -og corrected.gff3`

### Merge two GFF3 files ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* `gff3_merge` - Merge two GFF3 files
  * [gff3_merge readme](docs/gff3_merge.md)
  * [gff3_merge full documentation](docs/Merge-two-GFF3-files.md)
  * Quick start:
    * Merge the two file with auto-assignment of replace tags (default)
      `gff3_merge -g1 example_file/new_models.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -r merged_report.txt`
    * If your gff files have assigned proper replace tags at column 9 (Format: replace=[Transcript ID]), you could merge the two gff files without auto-assignment of tags.
      `gff3_merge -g1 example_file/new_models_w_replace.gff3 -g2 example_file/reference.gff3 -f example_file/reference.fa -og merged.gff -r merged_report.txt -noAuto`

### Sort a GFF3 file ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* `gff3_sort` - Sort a GFF3 file according to the order of Scaffold, coordinates on a Scaffold, and parent-child feature relationships
  * [gff3_sort readme](docs/gff3_sort.md)
  * Quick start:
    `gff3_sort -g example_file/example.gff3 -og example-sorted.gff3`

### Generate biological sequences from a GFF3 file ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* bin/gff3_to_fasta.py - extract biological sequences (such as spliced transcripts, cds, or peptides) from specific regions of genome based on a GFF3 file
  * [gff3_to_fasta readme](docs/gff3_to_fasta.md)
  * Quick start:
    `gff3_to_fasta -g example_file/example.gff3 -f example_file/reference.fa -st all -d simple -o test_sequences`

## Example Files ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* [example_file](example_file)/
  * Example files for testing

## Internal Dependencies ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* [gff3tool/lib/gff3](gff3tool/lib/gff3)/
  * Basic data structure used for nesting the information of genome annotations in GFF3 format.
* [gff3tool/lib/gff3_to_fasta](gff3tool/lib/gff3_to_fasta)/
  * Extract specific sequences from genome sequences according to the GFF3 file.
* [gff3tool/lib/ERROR](gff3tool/lib/ERROR)/
  * Contains the full list of Error codes and the corresponding Error tag
* [gff3tool/lib/function4gff](gff3tool/lib/function4gff)/
  * Functions for gff3 processing
* [gff3tool/lib/gff3/gff3.py](gff3tool/lib/gff3/gff3.py)
  * This program was contributed by Han Lin (http://gff3-py.readthedocs.org/en/latest/readme.html). Code was modified for customized usage.
* [gff3tool/lib/inter_model](gff3tool/lib/inter_model)/
  * QC functions for processing multiple features between models (inter-model) in a GFF3 file.
* [gff3tool/lib/intra_model](gff3tool/lib/intra_model)/
  * QC functions for processing multiple features within a model (intra-model) in a GFF3 file.
* [gff3tool/lib/single_feature](gff3tool/lib/single_feature)/
  * QC functions for processing single features in a GFF3 file.

