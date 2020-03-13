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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The error category 'Intra-model' collects formatting errors that can be
found by jointly considering multiple features within a gene model, such
as gene, mRNA, exon, and CDS features. Errors in this category are given
an 'Error\_Code' starting with 'Ema'.

+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Error\_Code   | Error\_Tag                                                                              | Checked if non-canonical   |
+===============+=========================================================================================+============================+
| Ema0001       | Parent feature start and end coordinates exceed those of child features                 | Yes                        |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0002       | Protein sequence contains internal stop codons                                          | No                         |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0003       | This feature is not contained within the parent feature coordinates                     | Yes                        |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0004       | Incomplete gene feature that should contain at least one mRNA, exon, and CDS            | No                         |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0005       | Pseudogene has invalid child feature type                                               | Yes                        |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0006       | Wrong phase                                                                             | No                         |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0007       | CDS and parent feature on different strands                                             | Yes                        |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0008       | Warning for distinct isoforms that do not share any regions                             | No                         |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+
| Ema0009       | Incorrectly merged gene parent? Isoforms that do not share coding sequences are found   | No                         |
+---------------+-----------------------------------------------------------------------------------------+----------------------------+

Inter-model: Multiple features across models (Emr)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The error category 'Inter-model' collects formatting errors that can be
found by comparing multiple gene models. Errors in this category are
given an 'Error\_Code' starting with 'Emr'.

+---------------+----------------------------------+----------------------------+
| Error\_Code   | Error\_Tag                       | Checked if non-canonical   |
+===============+==================================+============================+
| Emr0001       | Duplicate transcript found       | No                         |
+---------------+----------------------------------+----------------------------+
| Emr0002       | Incorrectly split gene parent?   | No                         |
+---------------+----------------------------------+----------------------------+
| Emr0003       | Duplicate ID                     | Yes                        |
+---------------+----------------------------------+----------------------------+

Single feature (Esf)
~~~~~~~~~~~~~~~~~~~

The error category 'Single Feature' collects formatting errors that can
be found by searching the GFF3 file line by line. Errors in this
category are given an 'Error\_Code' starting with 'Esf'.

+---------------+--------------------------------------------------------------------------+----------------------------+
| Error\_Code   | Error\_Tag                                                               | Checked if non-canonical   |
+===============+==========================================================================+============================+
| Esf0001       | Feature type may need to be changed to pseudogene                        | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0002       | Start/Stop is not a valid 1-based integer coordinate                     | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0003       | strand information missing                                               | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0004       | Seqid not found in any ##sequence-region                                 | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0005       | Start is less than the ##sequence-region start                           | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0006       | End is greater than the ##sequence-region end                            | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0007       | Seqid not found in the embedded ##FASTA                                  | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0008       | End is greater than the embedded ##FASTA sequence length                 | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0009       | Found Ns in a feature using the embedded ##FASTA                         | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0010       | Seqid not found in the external FASTA file                               | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0011       | End is greater than the external FASTA sequence length                   | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0012       | Found Ns in a feature using the external FASTA                           | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0013       | White chars not allowed at the start of a line                           | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0014       | ##gff-version" missing from the first line                               | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0015       | Expecting certain fields in the feature                                  | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0016       | ##sequence-region seqid may only appear once                             | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0017       | Start/End is not a valid integer                                         | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0018       | Start is not less than or equal to end                                   | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0019       | Version is not "3"                                                       | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0020       | Version is not a valid integer                                           | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0021       | Unknown directive                                                        | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0022       | Features should contain 9 fields                                         | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0023       | escape certain characters                                                | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0024       | Score is not a valid floating point number                               | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0025       | Strand has illegal characters                                            | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0026       | Phase is not 0, 1, or 2, or not a valid integer                          | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0027       | Phase is required for all CDS features                                   | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0028       | Attributes must escape the percent (%) sign and any control characters   | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0029       | Attributes must contain one and only one equal (=) sign                  | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0030       | Empty attribute tag                                                      | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0031       | Empty attribute value                                                    | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0032       | Found multiple attribute tags                                            | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0033       | Found ", " in a attribute, possible unescaped                            | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0034       | attribute has identical values (count, value)                            | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0035       | attribute has unresolved forward reference                               | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0036       | Value of a attribute contains unescaped ","                              | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0037       | Target attribute should have 3 or 4 values                               | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0038       | Start/End value of Target attribute is not a valid integer coordinate    | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0039       | Strand value of Target attribute has illegal characters                  | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0040       | Value of Is\_circular attribute is not "true"                            | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+
| Esf0041       | Unknown reserved (uppercase) attribute                                   | Yes                        |
+---------------+--------------------------------------------------------------------------+----------------------------+

