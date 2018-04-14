## Internal Dependencies of GFF3toolkit/lib
### Desciprtion of Functions
* [lib/gff3](lib/gff3)/
    - Basic data structure used for nesting the information of genome annotations in GFF3 format. 
    - Some of the error checking functions listed in [lib/ERROR](lib/ERROR)
* [lib/gff3_to_fasta](lib/gff3_to_fasta)/
    - Extract specific sequences from genome sequences according to the GFF3 file.
* [lib/ERROR](lib/ERROR)
    - Contains the full list of Error codes and the corresponding Error tag
* [lib/function4gff](lib/function4gff)/
    - Functions for gff3 processing
* lib/gff3/gff3.py
    - This program was contributed by Han Lin (http://gff3-py.readthedocs.org/en/latest/readme.html). Code was modified for customized usage.
* [lib/inter_model](lib/inter_model)/
    - QC functions for processing multiple features between models (inter-model) in a GFF3 file.
* [lib/intra_model](lib/intra_model)/
    - QC functions for processing multiple features within a model (intra-model) in a GFF3 file.
* [lib/single_feature](lib/single_feature)/
    - QC functions for processing single features in a GFF3 file.

### Functions used by each program (GFF3toolkit/bin/*.py)
* [bin/gff3_sort.py](bin/gff3_sort.py)/
    - [lib/gff3_/gff3_.py](lib/gff3/gff3.py)
* [bin/gff3_QC.py](bin/gff3_QC.py)
    - [lib/gff3_/gff3_.py](lib/gff3/gff3.py)
        - Note: If a error type cannot be found in the following four directories, you shall find it here
    - [lib/function4gff](lib/function4gff)/
    - [lib/inter_model](lib/inter_model)/
    - [lib/intra_model](lib/intra_model)/
    - [lib/single_feature](lib/single_feature)/
    - [lib/ERROR](lib/ERROR)

