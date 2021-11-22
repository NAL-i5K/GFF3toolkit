gff3\_QC full documentation
===========================

Background
----------

The GFF3 format is flexible and easy to use for most biologists, but
this flexibility also allows many errors to be introduced. This QC
program aims to detect over 50 types of formatting errors.

Errors are detected by reviewing three types of feature sets in a GFF3
file, and thus are grouped into three categories (Error category –
feature type): \* Intra-model errors (Ema) – multiple features within a
model \* Inter-model errors (Emr) – multiple features across models \*
Single feature errors (Esf) – each single feature.

In addition, we distinguish between errors that apply to protein-coding
genes in the `'canonical' Sequence ontology
style <https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md>`__,
and errors that apply to ‘non-canonical’ gene models – i.e. non-coding
models, or protein-coding genes that are not modeled with gene, mRNA,
CDS and exon features. To perform error-checking on a gff3 file that
contains non-canonical gene models, you can specify the –noncg argument
when running the program.

Below we list all errors currently considered by gff3\_QC.py, including
the error code, the error tag (a brief explanation of the error), and
whether the error is checked for non-canonical gene models (when using
the –noncg argument).

View the `gff3\_QC.py readme <gff3_QC.md>`__ for instructions on how to
run the program.

Intra-model: Multiple features within a model (Ema)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The error category 'Intra-model' collects formatting errors that can be
found by jointly considering multiple features within a gene model, such
as gene, mRNA, exon, and CDS features. Errors in this category are given
an 'Error\_Code' starting with 'Ema'.

+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Error\_Code   | Error\_level  | Error\_Tag                                                                              | Checked if non-canonical   |
+===============+===============+=========================================================================================+============================+
| Ema0001       | Warning       | Parent feature start and end coordinates exceed those of child features                 | Yes                        |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0002       | Warning       | Protein sequence contains internal stop codons                                          | No                         |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0003       | Warning       | This feature is not contained within the parent feature coordinates                     | Yes                        |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0004       | Info          | Incomplete gene feature that should contain at least one mRNA, exon, and CDS            | No                         |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0005       | Info          | Pseudogene has invalid child feature type                                               | Yes                        |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0006       | Info          | Wrong phase                                                                             | No                         |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0007       | Warning       | CDS and parent feature on different strands                                             | Yes                        |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0008       | Warning       | Warning for distinct isoforms that do not share any regions                             | No                         |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0009       | Warning       | Incorrectly merged gene parent? Isoforms that do not share coding sequences are found   | No                         |
+---------------+---------------+-----------------------------------------------------------------------------------------+----------------------------+

Inter-model: Multiple features across models (Emr)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The error category 'Inter-model' collects formatting errors that can be
found by comparing multiple gene models. Errors in this category are
given an 'Error\_Code' starting with 'Emr'.

+---------------+---------------+----------------------------------+----------------------------+
| Error\_Code   | Error\_level  | Error\_Tag                       | Checked if non-canonical   |
+===============+===============+==================================+============================+
| Emr0001       | Warning       | Duplicate transcript found       | No                         |
+---------------+---------------+----------------------------------+----------------------------+
| Emr0002       | Warning       | Incorrectly split gene parent?   | No                         |
+---------------+---------------+----------------------------------+----------------------------+
| Emr0003       | Error         | Duplicate ID                     | Yes                        |
+---------------+---------------+----------------------------------+----------------------------+

Single feature (Esf)
~~~~~~~~~~~~~~~~~~~~

The error category 'Single Feature' collects formatting errors that can
be found by searching the GFF3 file line by line. Errors in this
category are given an 'Error\_Code' starting with 'Esf'.

+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Error\_Code   | Error\_level  | Error\_Tag                                                               | Checked if non-canonical   |
+===============+===============+==========================================================================+============================+
| Esf0001       | Info          | Feature type may need to be changed to pseudogene                        | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0002       | Error         | Start/Stop is not a valid 1-based integer coordinate                     | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0003       | Error         | strand information missing                                               | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0004       | Error         | Seqid not found in any ##sequence-region                                 | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0005       | Error         | Start is less than the ##sequence-region start                           | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0006       | Error         | End is greater than the ##sequence-region end                            | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0007       | Error         | Seqid not found in the embedded ##FASTA                                  | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0008       | Error         | End is greater than the embedded ##FASTA sequence length                 | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0009       | Info          | Found Ns in a feature using the embedded ##FASTA                         | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0010       | Error         | Seqid not found in the external FASTA file                               | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0011       | Error         | End is greater than the external FASTA sequence length                   | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0012       | Info          | Found Ns in a feature using the external FASTA                           | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0013       | Error         | White chars not allowed at the start of a line                           | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0014       | Error         | ##gff-version" missing from the first line                               | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0015       | Error         | Expecting certain fields in the feature                                  | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0016       | Error         | ##sequence-region seqid may only appear once                             | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0017       | Error         | Start/End is not a valid integer                                         | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0018       | Error         | Start is not less than or equal to end                                   | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0019       | Info          | Version is not "3"                                                       | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0020       | Error         | Version is not a valid integer                                           | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0021       | Info          | Unknown directive                                                        | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0022       | Error         | Features should contain 9 fields                                         | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0023       | Error         | escape certain characters                                                | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0024       | Error         | Score is not a valid floating point number                               | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0025       | Error         | Strand has illegal characters                                            | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0026       | Error         | Phase is not 0, 1, or 2, or not a valid integer                          | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0027       | Error         | Phase is required for all CDS features                                   | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0028       | Info          | Attributes must escape the percent (%) sign and any control characters   | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0029       | Error         | Attributes must contain one and only one equal (=) sign                  | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0030       | Error         | Empty attribute tag                                                      | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0031       | Error         | Empty attribute value                                                    | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0032       | Error         | Found multiple attribute tags                                            | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0033       | Info          | Found ", " in a attribute, possible unescaped                            | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0034       | Info          | attribute has identical values (count, value)                            | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0035       | Info          | attribute has unresolved forward reference                               | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0036       | Info          | Value of a attribute contains unescaped ","                              | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0037       | Error         | Target attribute should have 3 or 4 values                               | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0038       | Error         | Start/End value of Target attribute is not a valid integer coordinate    | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0039       | Error         | Strand value of Target attribute has illegal characters                  | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0040       | Error         | Value of Is\_circular attribute is not "true"                            | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0041       | Error         | Unknown reserved (uppercase) attribute                                   | Yes                        |
+---------------+---------------+--------------------------------------------------------------------------+----------------------------+

