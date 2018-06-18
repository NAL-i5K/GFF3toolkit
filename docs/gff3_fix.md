# gff3_fix.py

## Usage 

gff3_fix.py [-h] [-qc_r QC_REPORT] [-g GFF] [-og OUTPUT_GFF] [-v]

## Testing environment

Python 2.7

## Inputs
1. Error report: Error report from gff3_QC.py. Specify the file name with the -qc_r or --qc_report argument. Error report should only include those errors that should be fixed. If errors identified by gff3_QC.py should not be fixed, remove lines containing errors from report file. 
2. GFF3: Specify the file name with the -g or --gff argument.


## Outputs
1. Corrected GFF3

## Quick start
`gff3_fix -qc_r error.txt -g example_file/example.gff3 -og corrected.gff3`

## Optional arguments

1.  -h, --help            
    - show this help message and exit
2.  -qc_r QC_REPORT, --qc_report QC_REPORT
    - Error report from gff3_QC.py
3.  -g GFF, --gff GFF
    - Genome annotation file, gff3 format
4.  -og OUTPUT_GFF, --output_gff OUTPUT_GFF
    - output gff3 file name (default: corrected.gff3)
5.  -v, --version         
    - show program's version number and exit

## More information
- [gff3_fix.py full documentation](https://github.com/NAL-i5K/GFF3toolkit/wiki/gff3_fix.py-documentation)
