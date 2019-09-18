# gff3_to_fasta readme

Extract sequences from specific regions of genome based on gff file.

## Features

* **Incorporation of [gff3.py](https://github.com/hotdogee/gff3-py)**: `gff3.py` is contributed by [Han Lin](https://github.com/hotdogee) which uses simple data structures to parse a [`GFF3`] file into a structure composed of simple python [`dict`] and [`list`].
* **Validation**: Validate the [GFF3 formatting errors](Detection-of-GFF3-format-errors.md) utilizing [QC methods](tree/master/bin/gff-QC.py) contributed by the [I5K Workspace@NAL team](https://i5k.nal.usda.gov/). Provide `WARNING` messages for gene models that may have incorrect biological sequences generated because of [`GFF3`] formatting errors.
* **Easy extraction of biological sequences**: Provide options for extracting six types of biological sequences or user-specified type of spliced sequences.
    - **`gene`**: Gene sequence for each record in the [`FASTA`] output. Gene or pseudogene features need to be included in the gff file
    - **`exon`**: Exon sequence for each record in the [`FASTA`] output. Exon features need to be included in the gff file
    - **`pre_trans`**: Genomic region of a transcript model, namely premature transcript (exon and intron regions included), for each record in the [`FASTA`] output. Transcript-level features (such as mRNA, rRNA, pseudogenic transcripts) need to be included in the gff file.
    - **`trans`**: Spliced transcript (only exons included) for each record in the [`FASTA`] output. Exon features are mainly used for splicing. CDS features are used instead if exon features are absent. If both cds and exon features are absent, the transcript is not generated and a `WARNING` message is shown with the transcript ID.
    - **`cds`**: Coding sequence (utr exons and introns excluded) for each record in the [`FASTA`] output. CDS features need to be included in the gff file.
    - **`pep`**: Translated peptide sequences (translation based on cds regions) for each record in the [`FASTA`] output. CDS features need to be included in the gff file.
    - **`user_defined`**: Specify parent and child features for fasta extraction via the -u argument, format [parent feature type] [child feature type].(e.g. `-st user_defined -u miRNA exon`)
* **`translator` method for universal translation**: The `translator` method is feasible for
    - translation from 64 combitions of [standard codons](https://en.wikipedia.org/wiki/DNA_codon_table) (Only standard codons and universal stop condons are considered.)
    - translation from [codons with IUB Depiction](https://en.wikipedia.org/wiki/DNA_codon_table)
    - translation from mRNA (U contained) or CDS (T, instead of U contained)

## Usage

gff3_to_fasta.py [-h] [-g GFF] [-f FASTA] [-st SEQUENCE_TYPE] [-u USER_DEFINED] [-d DEFLINE] [-o OUTPUT_PREFIX] [-noQC] [-v]

## Testing enviroment
1. Python 2.7

## Required inputs

1. GFF3: specify the file name with the -g argument
2. Fasta file: specify the file name with the -f argument. This file **must** be the Fasta file that the GFF3 seqids and coordinates refer to. For more information, refer to the [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md).
3. Output prefix: specify with the -o argument. All resulting fasta files will contain this prefix.

## Outputs

1. Fasta formatted sequence file based on the gff3 file.

## Example command

1. Specify the input, output file names and options using short arguments:
    - `gff3_to_fasta -g example_file/example.gff3 -f example_file/reference.fa -st all -d simple -o test_sequences`

## Optional arguments

1. -h, --help
    - show this help message and exit
2. -g GFF, --gff GFF
    - Genome annotation file in GFF3 format
3. -f FASTA, --fasta FASTA
    - Genome sequences in FASTA format
4. -embf, --embedded_fasta
    - Specify this option if you want to extract sequence from embedded fasta.
5. -st SEQUENCE_TYPE, --sequence_type SEQUENCE_TYPE
    - Type of sequences you would like to extract:
        * "all" - FASTA files for all types of sequences listed below, except user_defined;
        * "gene" - gene sequence for each record;
        * "exon" - exon sequence for each record;
        * "pre_trans" - genomic region of a transcript model (premature transcript);
        * "trans" - spliced transcripts (only exons included);
        * "cds" - coding sequences;
        * "pep" - peptide sequences;
        * "user_defined" - specify parent and child features via the -u argument.
6. -u USER_DEFINED, --user_defined USER_DEFINED
    - Specify parent and child features for fasta extraction, format [parent feature type] [child feature type]. Required if -st user_defined is given.
        * Example: -st user_defined -u miRNA exon
	* Lines with the child feature type given in -u must contain a Parent attribute referencing the given Parent feature type. Hence, the parent lines must also contain an ID attribute.
	* If CDS is the child feature type, the program will take phase into account.
7. -d DEFLINE, --defline DEFLINE
    - Defline format in the output FASTA file:
        * "simple" - only ID is shown in the defline;
        * "complete" - complete information of the feature is shown in the defline.
8. -o OUTPUT_PREFIX, --output_prefix OUTPUT_PREFIX
    - Prefix of output file name
9. -noQC, --quality_control
    - Specify this option if you do not want to excute quality control for gff file. (default: QC is executed)
10. -v, --version
    - Show program version number and exit

