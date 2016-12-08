# GFF3toolkit
Python programs for processing GFF3 files

## QC and OGS generation pipeline by I5K Workspace@NAL
This project is to develop python tools for generating official gene set (OGS) by integrating manually curated and predicted gene annotations (GFF3 format). There are two phases involved: (1) QC phase and (2) Merge phase. A prototype of the whole pipeline has been done by I5K Workspace@NAL team. However, the source codes of the prototype program is not release for public, because it incorporated several components written by programming languages other than Python. Therefore, this project will re-implement those non-python components, and expects to deliver a complete python package for OGS generation. If you have urgent needs for OGS generation, you can send queries to I5K [at] ars.usda.gov. The i5k team can help to host your data, and apply OGS generation pipeline on your data for you.

[Wiki page for QC and OGS generation pipeline by I5K Workspace@NAL](https://github.com/NAL-i5K/I5KNAL_OGS/wiki)

### bin/
General script for running through different phases of the OGS pipeline.
* gff-QC.py
    - Detection of GFF format errors (~50 types of errors. Details can be found in [wiki page](https://github.com/NAL-i5K/I5KNAL_OGS/wiki/QC-phase))

### example_file/
* Example files for testing

### \_\_develop\_\_/
Tools under development.
* function4gff/
    - Functions for dealing with gff3
* inter_model/
    - QC functions for processing multiple features between models (inter-model) in GFF3 file.
* intra_model/
    - QC functions for processing multiple features within a model (intra-model) in GFF3 file.
* single_feature/
    - QC functions for processing every single feature in GFF3 file.
* template/
    - Template script for development

### lib/
Completed tools would be shown as under a specific directory. Tools under development would be shown as a Symbolic link.
* [gff3_modified](https://github.com/NAL-i5K/I5KNAL_OGS/tree/I5KNAL_OGS/lib/gff3_modified)/
    - Basic data structure used for nesting the information of genome annotations in GFF3 format.
* [gff3_to_fasta](https://github.com/NAL-i5K/I5KNAL_OGS/tree/I5KNAL_OGS/lib/gff3_to_fasta)/
    - Extract specific sequeces from genome sequences accroding to gff file.

## Sort a GFF3 file

### bin/

* gff3-sort.py: Sort a GFF3 file according to the order of Scaffold, coordinates on a Scaffold, and feature relationship based on sequence ontology

### lib/
* gff3.py: This program was contributed by Han Lin (http://gff3-py.readthedocs.org/en/latest/readme.html). Codes were modified for customized usage.
 
## Genernate biological sequences from a GFF3 file

### bin/
* gff3_to_fasta.py: The software is used to extract biological sequences (such as spliced transcripts, cds, or peptides) from specific regions of genome based on a GFF3 file. Please check the details [here](https://github.com/NAL-i5K/GFF3toolkit/tree/master/lib/gff3_to_fasta).

