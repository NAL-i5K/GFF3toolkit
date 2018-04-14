# gff3-to-fasta

This software extracts biological sequences (such as spliced transcripts, cds, or peptides) from specific regions of a genomic fasta file based on a given [`GFF3`] file.
* Free software: [license](https://github.com/NAL-i5K/GFF3toolkit/blob/master/LICENCE.md)

## Features

* **Incorporation of [gff3.py](https://github.com/hotdogee/gff3-py)**: `gff3.py` is contributed by [Han Lin](https://github.com/hotdogee) which uses simple data structures to parse a [`GFF3`] file into a structure composed of simple python [`dict`] and [`list`].
* **Validation**: Validate the [GFF3 formatting errors](https://github.com/NAL-i5K/I5KNAL_OGS/wiki/QC-phase) utilizing [QC methods](tree/master/bin/gff-QC.py) contributed by the [I5K Workspace@NAL team](https://i5k.nal.usda.gov/). Provide `WARNING` messages for gene models that may have incorrect biological sequences generated because of [`GFF3`] formatting errors.
* **Easy extraction of biological sequences**: Provide options for extracting six types of biological sequences.
    - **`gene`**: Gene sequence for each record in the [`FASTA`] output. Gene or pseudogene features need to be included in the gff file
    - **`exon`**: Exon sequence for each record in the [`FASTA`] output. Exon features need to be included in the gff file
    - **`pre_trans`**: Genomic region of a transcript model, namely premature transcript (exon and intron regions included), for each record in the [`FASTA`] output. Transcript-level features (such as mRNA, rRNA, pseudogenic transcripts) need to be included in the gff file.
    - **`trans`**: Spliced transcript (only exons included) for each record in the [`FASTA`] output. Exon features are mainly used for splicing. CDS features are used instead if exon features are absent. If both cds and exon features are absent, the transcript is not generated and a `WARNING` message is shown with the transcript ID.
    - **`cds`**: Coding sequence (utr exons and introns excluded) for each record in the [`FASTA`] output. CDS features need to be included in the gff file.
    - **`pep`**: Translated peptide sequences (translation based on cds regions) for each record in the [`FASTA`] output. CDS features need to be included in the gff file.
* **`translator` method for universal translation**: The `translator` method is feasible for 
    - translation from 64 combitions of [standard codons](http://www-bimas.cit.nih.gov/molbio/translate/codes.html) (Only standard codons and universal stop condons are considered.)
    - translation from [codons with IUB Depiction](http://www-bimas.cit.nih.gov/molbio/translate/codes.html)
    - translation from mRNA (U contained) or CDS (T, instead of U contained)

## Quick Start

Sequence extraction based on genome annotation file in [`GFF3`] format might generate incorrect sequences if the [`GFF3`] file contains certain errors. This program can automatically validate [`GFF3`] format and list the detected errors for users along with the extracted sequences by simple command as follows:

`python gff3-to-fasta.py -g example_file/annotations3.gff -f example_file/sample.fa -st cds -d simple -o sample_output`

If you would like to ignore the QC step for checking errors in gff file, you can use the below command:

`python gff3-to-fasta.py -g example_file/annotations3.gff -f example_file/sample.fa -st cds -d simple -o sample_output -noQC`

If you would like to incorporate a specfic method in `gff3-to-fasta` into other python script, below is a suggested script.

```python
    import gff3_to_fasta

    seq = 'GTGGCTCGTTTGATTGAACAAATATGTACTAACCCAGTTGGATTATCTGGATCTGGATTTTTTCTGGTGACAAAGAATTTTCTACTTCAGATGGCAGGAACGATAGTTACATTTGAACTGATGCTGTTTCAATTTGCCCCAGTAAATGCACAGCAAAAACCCATGAAGTCATATGACTGTATTTAA'

    pep = gff3_to_fasta.translator(seq)
    print 'Input: {0:s}'.format(seq)
    print 'Translation: {0:s}'.format(pep)
```


## Options

```
usage: gff3-to-fasta.py [-h] [-g GFF] [-f FASTA] [-st SEQUENCE_TYPE]
                        [-d DEFLINE] [-o OUTPUT_PREFIX] [-noQC] [-v]
```

* `-h` (--help): Show help message and exit
* `-g` (GFF, --gff GFF): Genome annotation file in GFF3 format. The sequence IDs in the GFF3 file **must** correspond to the sequence IDs in the given FASTA file. 
* `-f` (FASTA, --fasta): Genome sequence file in FASTA format. 
* `-st` (SEQUENCE_TYPE, --sequence_type): Type of sequences you would like to extract. It must be one of the options below.
    - all - FASTA files for all types of sequences listed below
    - gene - gene sequence for each record
    - exon - exon sequence for each record
    - pre_trans - genomic region of a transcript model (premature transcript)
    - trans - spliced transcripts (only exons included)
    - cds - coding sequences
    - pep - peptide seuqences
* `-d` (DEFLINE, --defline): Specify defline format. It must be one of the options below.
    - simple - only ID is shown in the defline; eg. `>LDEC008409-PA`
    - complete - complete information of the feature is shown in the defline; eg. `>Scaffold194:420160..444997:-|peptide|Parent=LDEC008409|ID=LDEC008409-PA|Name=LDEC008409-PA`
* `-o` (OUTPUT_PREFIX, --output_prefix): Prefix of output file name
* `-noQC` (--quality_control): Specify this option if you do not want to execute quality control of the gff3 file, otherwise QC will be executed while running the program. (default: QC is executed)
* `-v` (--version): Show program's version number and exit


[`GFF3`]: http://www.sequenceontology.org/gff3.shtml
[`dict`]: https://docs.python.org/2/tutorial/datastructures.html#dictionaries
[`list`]: https://docs.python.org/2/tutorial/datastructures.html#more-on-lists
[`FASTA`]: http://en.wikipedia.org/wiki/FASTA_format


