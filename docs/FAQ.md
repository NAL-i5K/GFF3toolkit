# FAQ

## Q: When installing, the program fails with following message: `ImportError: No module named wheel.bdist_wheel`.

Since 1.4.2, we use [wheel](https://pythonwheels.com/) to build our python package. This error message means that you don't have [wheel](https://pythonwheels.com/) on your machine. Use `pip install wheel` to install it first.

## Q: When running one of the GFF3-toolkit programs, the program fails with a stack trace error. 

Usually, this means that there is a problem with the input file. We are working on having each program output error messages with the input file line number. In the meantime, send us your input file and we can help figure out what the problem is. 

## Q: What are the licensing terms for this project?

This software/database is a "United States Government Work" under the terms of the United States Copyright Act. It was written as part of the author's official duties as a United States Government employee and thus cannot be copyrighted. This software/database is freely available to the public for use. The National Agriculture Library and the U.S. Government have not placed any restriction on its use or reproduction. (Please see [LICENCE.md](https://github.com/NAL-i5K/GFF3toolkit/blob/master/LICENCE.md))

## Q: What kind of errors can be detected by gff3_QC.py? (Detection of GFF3 format errors: gff3_QC.py)

Currently, ~50 types of formatting errors can be detected. Errors are detected by reviewing three types of feature sets in a GFF3 file, and thus are grouped into three categories (Error category – feature type): 
* Intra-model errors (Ema) – multiple features within a model
* Inter-model errors (Emr) – multiple features across models
* Single feature errors (Esf) – each single feature.

Please view the full documentation of [gff3_QC.py](Detection-of-GFF3-format-errors.md) for the full list of detected error types.

## Q: Why is gff3_QC.py taking so long to run? (Detection of GFF3 format errors: gff3_QC.py)

gff3_QC.py can take a while if your gff3 file is large - please be patient!

## Q: Why does the sorted gff3 file have a different number of lines than the input file? (Sort a GFF3 file: gff3_sort.py)

The program gff3_sort.py automatically ignores the hash tag lines other than ##gff-version 3 and ### while sorting a GFF3 file. After sorting, the program puts one line of ### between every gene model in the output GFF3. Therefore, the total lines of the output file might be different from the input. To check the consistency of the lines, please use the following command,

>  grep -v "#" input.gff |wc -l

>  grep -v "#" sorted.gff |wc -l

In addition, if your input gff file contains a feature that has two or more parent IDs, the program replicates the feature and lists it under each parent. Thus, the output file would have more lines than the input file. 

## Q: Which codons are considered for translation? (Generate biological sequences from a GFF3 file: gff3_to_fasta.py)

Translation from 64 combinations of [standard codons](https://www-bimas.cit.nih.gov/molbio/translate/codes.html) (Only standard codons and universal stop codons are considered.)

## Q: Why does gff3_merge.py sometimes reject auto-assigned replace tags when the reference model has multiple isoforms? (Merge 2 GFF3 files: gff3_merge.py)

It is possible for a modified model to have multiple isoforms that do not share CDS with each other - for example with partial models due to a poor genome assembly. In this case, the auto-assignment program will assign different replace tags to each isoform, but will then reject these auto-assigned replace tags because it expects isoforms of a gene model to have the same replace tags (see section "Some notes on multi-isoform models", above). You'll need to add the replace tags manually - all isoforms should carry the replace tags of all models to be replaced by the whole gene model.
