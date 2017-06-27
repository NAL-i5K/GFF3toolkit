# gff-QC.py

## Usage 

gff-QC.py [-h] [-g GFF] [-f FASTA] [-o OUTPUT] [-v]

## Testing environment

Python 2.7

## Inputs
1. GFF3: Specify the file name with the -g or --gff argument. Please note that this program requires gene/pseudogene and mRNA/pseudogenic_transcript to have an ID attribute in column 9.
2. Fasta file: Specify the file name with the -f or --fasta argument. This file **must** be the Fasta file that the GFF3 seqids and coordinates refer to. For more information, refer to the [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md).

## Outputs
1. Error report for the input GFF3 file
    * Line_num: Line numbers of the found problematic models in the input GFF3 file.
    * Error_code: Error codes for the found problematic models. Please refer to lib/ERROR/ERROR.py to see the full list of Error_code and the corresponding Error_tag.
        * Error_tag: Detail of the found errors for the problematic models. Please refer to lib/ERROR/ERROR.py to see the full list of Error_code and the corresponding Error_tag.

## Quick start
`python2.7 bin/gff-QC.py -g example_file/example.gff3 -f example_file/reference.fa -o test`

or

`python2.7 bin/gff-QC.py --gff example_file/example.gff3 --fasta example_file/reference.fa --output test`

## Optional arguments

1.  -h, --help            
    - show this help message and exit
2.  -g GFF, --gff GFF     
    - Genome annotation file, gff3 format
3.  -f FASTA, --fasta FASTA
    - Genome sequences, fasta format
4.  -o OUTPUT, --output OUTPUT
    - output file name (default: report.txt)
5.  -v, --version         
    - show program's version number and exit

## Background

The GFF3 format is flexible and easy to use for most biologists, but this flexibility also allows many errors to be introduced. This QC program aims to detect over 50 types of formatting errors.

Errors are detected by reviewing three types of feature sets in a GFF3 file, and thus are grouped into three categories (Error category – feature type): 
* Intra-model errors (Ema) – multiple features within a model
* Inter-model errors (Emr) – multiple features across models
* Single feature errors (Esf) – each single feature.

Below are listed all errors currently considered by gff-QC.py, including the error code, the error tag (a brief explanation of the error), and a note whether the error is fully implemented in gff-QC.py.

### Intra-model: Multiple features within a model (Ema)
The error category 'Intra-model' collects formatting errors that can be found by jointly considering multiple features within a gene model, such as gene, mRNA, exon, and CDS features. Errors in this category are given an 'Error_Code' starting with 'Ema'. 

|Error_Code|Error_Tag|Note|
|:------|:------|:-----|
|Ema0001|redundant length of the gene|Done|
|Ema0002|internal stops|Done|
|Ema0003|This feature is not contained within the feature boundaries of parent|Done|
|Ema0004|Incomplete gene feature that should be contain at least one mRNA, exon, and CDS|Done|
|Ema0005|unusual child features in the type of pseudogene found|Done|
|Ema0006|Wrong phase|Done|
|Ema0007|Inconsistent CDS strand with parent|Done|

### Inter-model: Multiple features across models (Emr)
The error category 'Inter-model' collects formatting errors that can be found by comparing multiple gene models. Errors in this category are given an 'Error_Code' starting with 'Emr'. 

|Error_Code|Error_Tag|Note|
|:------|:------|:-----|
|Emr0001|Duplicate transcript found|Done|
|Emr0002|wrongly merged gene parent?|**_TBA_**|
|Emr0003|wrongly split gene parent?|**_TBA_**|
|Emr0004|models with distant isoforms|**_TBA_**|
|Emr0005|Duplicate ID|Done|

### Single feature (Esf)
The error category 'Single Feature' collects formatting errors that can be found by searching the GFF3 file line by line. Errors in this category are given an 'Error_Code' starting with 'Esf'. 

|Error_Code|Error_Tag|Note|
|:------|:------|:-----|
|Esf0001|pseudogene or not?|Done|
|Esf0002|Negative/Zero start/end coordinate|Done|
|Esf0003|strand information missing|**_TBA_**|
|Esf0004|Seqid not found in any ##sequence-region|Done|
|Esf0005|Start is less than the ##sequence-region start|Done|
|Esf0006|End is greater than the ##sequence-region end|Done|
|Esf0007|Seqid not found in the embedded ##FASTA|Done|
|Esf0008|End is greater than the embedded ##FASTA sequence length|Done|
|Esf0009|Found Ns in a feature using the embedded ##FASTA|Done|
|Esf0010|Seqid not found in the external FASTA file|Done|
|Esf0011|End is greater than the external FASTA sequence length|Done|
|Esf0012|Found Ns in a feature using the external FASTA|Done|
|Esf0013|White chars not allowed at the start of a line|Done|
|Esf0014|##gff-version" missing from the first line|Done|
|Esf0015|Expecting certain fields in the feature|Done|
|Esf0016|##sequence-region seqid may only appear once|Done|
|Esf0017|Start/End is not a valid integer|Done|
|Esf0018|Start is not less than or equal to end|Done|
|Esf0019|Version is not "3"|Done|
|Esf0020|Version is not a valid integer|Done|
|Esf0021|Unknown directive|Done|
|Esf0022|Features should contain 9 fields|Done|
|Esf0023|escape certain characters|Done|
|Esf0024|Score is not a valid floating point number|Done|
|Esf0025|Strand has illegal characters|Done|
|Esf0026|Phase is not 0, 1, or 2, or not a valid integer|Done|
|Esf0027|Phase is required for all CDS features|Done|
|Esf0028|Attributes must escape the percent (%) sign and any control characters|Done|
|Esf0029|Attributes must contain one and only one equal (=) sign|Done|
|Esf0030|Empty attribute tag|Done|
|Esf0031|Empty attribute value|Done|
|Esf0032|Found multiple attribute tags|Done|
|Esf0033|Found ", " in a attribute, possible unescaped|Done|
|Esf0034|attribute has identical values (count, value)|Done|
|Esf0035|attribute has unresolved forward reference|Done|
|Esf0036|Value of a attribute contains unescaped ","|Done|
|Esf0037|Target attribute should have 3 or 4 values|Done|
|Esf0038|Start/End value of Target attribute is not a valid integer coordinate|Done|
|Esf0039|Strand value of Target attribute has illegal characters|Done|
|Esf0040|Value of Is_circular attribute is not "true"|Done|
|Esf0041|Unknown reserved (uppercase) attribute|Done|
