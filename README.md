# GFF3toolkit - Python programs for processing GFF3 files
* Current functions
    - [Detect GFF3 format errors](#detect-gff3-format-errors-back)
    - [Sort a GFF3 file](#sort-a-gff3-file-back)
    - [Generate biological sequences from a GFF3 file](#generate-biological-sequences-from-a-gff3-file-back)

## Background

The [GFF3 format](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md) (Generic Feature Format Version 3) is one of the standard formats to describe and represent genomic features. It is an incredibly flexible, 9-column format, which is easily manipulated by biologists. This flexibility, however, makes it very easy to break the format. We have developed the GFF3toolkit to help identify common problems with GFF3 files; sort GFF3 files (which can aid in using down-stream processing programs and custom parsing); and generate FASTA files from a GFF3 file for many use cases (e.g. feature types beyond mRNA).

## Detect GFF3 format errors ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* bin/gff-QC.py 
    - [Documentation page](gff-QC.md)
    - Detection of GFF format errors (~50 types of errors. Details can be found in [wiki page](https://github.com/NAL-i5K/I5KNAL_OGS/wiki/QC-phase)
    - Please refer to lib/ERROR/ERROR.py to see the full list of Error codes and the corresponding Error tags.
    - Quick start:
        `python2.7 GFF3toolkit/bin/gff-QC.py -g GFF3toolkit/example_file/annotations2.gff -f GFF3toolkit/example_file/sample.fa -o test2.txt`
    - Note - Longer GFF3 files will take longer to process.

## Sort a GFF3 file ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* bin/gff3-sort.py
    - [Documentation page](gff3-sort.md)
    - Sort a GFF3 file according to the order of Scaffold, coordinates on a Scaffold, and feature relationship based on sequence ontology
    - Quick start:
        `python2.7 GFF3toolkit/bin/gff3-sort.py -g GFF3toolkit/example_file/annotations2.gff -og annotations2-sorted.gff`

## Generate biological sequences from a GFF3 file ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* bin/gff3_to_fasta.py
    - [Documentation page](tree/master/lib/gff3_to_fasta)
    - The software is used to extract biological sequences (such as spliced transcripts, cds, or peptides) from specific regions of genome based on a GFF3 file. Please check the details [here](https://github.com/NAL-i5K/GFF3toolkit/tree/master/lib/gff3_to_fasta).
    - Quick start:
        `python2.7 GFF3toolkit/bin/gff3_to_fasta.py -g GFF3toolkit/example_file/annotations2.gff -f GFF3toolkit/example_file/sample.fa -st all -d simple -o test_sequences`

## Example Files ([back](#gff3toolkit---python-programs-for-processing-gff3-files))

* example_file/
    - Example files for testing

## Internal Dependencies ([back](#gff3toolkit---python-programs-for-processing-gff3-files))
* [lib/gff3_modified](lib/gff3_modified)/
    - Basic data structure used for nesting the information of genome annotations in GFF3 format.
* [lib/gff3_to_fasta](lib/gff3_to_fasta)/
    - Extract specific sequences from genome sequences according to the GFF3 file.
* [lib/ERROR](lib/ERROR)
    - Contains the full list of Error codes and the corresponding Error tag
* [lib/function4gff](lib/function4gff)/
    - Functions for gff3 processing
* lib/gff3.py
    - This program was contributed by Han Lin (http://gff3-py.readthedocs.org/en/latest/readme.html). Code was modified for customized usage.
* [lib/inter_model](lib/inter_model)/
    - QC functions for processing multiple features between models (inter-model) in a GFF3 file.
* [lib/intra_model](lib/intra_model)/
    - QC functions for processing multiple features within a model (intra-model) in a GFF3 file.
* [lib/single_feature](lib/single_feature)/
    - QC functions for processing single features in a GFF3 file.