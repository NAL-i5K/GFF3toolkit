#! /usr/local/bin/python2.7
# Contributed by Mei-Ju Chen <arbula [at] gmail [dot] com> (2015)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import sys
import re
import logging
import string
# try to import from project first
from os.path import dirname
if dirname(__file__) == '':
    lib_path = '../../lib'
else:
    lib_path = dirname(__file__) + '/../../lib'
sys.path.insert(1, lib_path)
from gff3_modified import Gff3
import function4gff
import intra_model
import single_feature

__version__ = '0.0.1'

COMPLEMENT_TRANS = string.maketrans('TAGCtagc', 'ATCGATCG')
def complement(seq):
    return seq.translate(COMPLEMENT_TRANS)

def get_subseq(gff, line):
    string = gff.fasta_external[line['seqid']]['seq'][(line['start']-1):line['end']]
    if line['strand'] == '-':
        string = complement(string[::-1])
    return string

# Features of the translation funtion of this program,
# 1. translation from 64 combitions of codons
# 2. translation from codons with IUB Depiction
# 3. translation from mRNA (U contained) or CDS (T, instead of U contained)
BASES = ['T', 'C', 'A', 'G']
CODONS = [a+b+c for a in BASES for b in BASES for c in BASES]
CODONS.extend(['GCN', 'TGY', 'GAY', 'GAR', 'TTY', 'GGN', 'CAY', 'ATH', 'AAR', 'TTR', 'CTN', 'YTR', 'AAY', 'CCN', 'CAR', 'CGN', 'AGR', 'MGR', 'TCN', 'AGY', 'ACN', 'GTN', 'NNN', 'TAY', 'TAR', 'TRA']) # IUB Depiction
AMINO_ACIDS = 'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGGACDEFGHIKLLLNPQRRRSSTVXY**'
CODON_TABLE = dict(zip(CODONS, AMINO_ACIDS))
def translator(seq):
    seq = seq.upper().replace('\n', '').replace(' ', '').replace('U', 'T')
    peptide = ''
    for i in xrange(0, len(seq), 3):
        codon = seq[i: i+3]
        amino_acid = CODON_TABLE.get(codon, '!')
        if amino_acid != '!': # end of seq
            peptide += amino_acid
    return peptide

def splicer(gff, ftype, dline):
    seq=dict()
    roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    for root in roots:
        #if ftype[0] == 'CDS' and root['type'] == 'pseudogene': # pseudogene should not contain cds
            #continue
        rid = 'NA'
        if root['attributes'].has_key('ID'):
           rid = root['attributes']['ID']
       
        children = root['children']
        for child in children:
            cid = 'NA'
            if child['attributes'].has_key('ID'):
                cid = child['attributes']['ID']
            cname = cid
            if child['attributes'].has_key('Name'):
                cname = child['attributes']['Name']
            defline='>{0:s}'.format(cid)
            if ftype[0] == 'CDS':
                defline='>{0:s}-CDS'.format(cid)
            if dline == 'complete':
                defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}({8:s})|Parent={5:s}|ID={6:s}|Name={7:s}'.format(child['seqid'], child['start'], child['end'], child['strand'], child['type'], rid, cid, cname, ftype[0])

            segments = []
            gchildren = child['children']
            for gchild in gchildren:
                if gchild['type'] in ftype:
                    segments.append(gchild)
            
            flag = 0
            if len(segments)==0:
                flag += 1
                for gchild in gchildren:
                    if gchild['type'] == 'CDS':
                        segments.append(gchild)

            if len(segments)==0 and ftype[0] == 'CDS':
                flag += 1
                print("WARNING  There is no CDS feature for {0:s} in the input gff. The sequence of {0:s} is not generated.".format(cid))
                continue
            elif len(segments)==0:
                flag += 1
                print("WARNING  There is no exon, nor CDS feature for {0:s} in the input gff. The sequence of {0:s} is not generated.".format(cid))
                continue
            
            if flag == 1:
                print("WARNING  There is no exon feature for {0:s} in the input gff. CDS features are used for splicing instead.".format(cid))
            
            sort_seg = function4gff.featureSort(segments)
            if gchild['strand'] == '-':
                sort_seg = function4gff.featureSort(segments, reverse=True)

            tmpseq = ''
            for s in sort_seg:
                tmpseq = tmpseq + get_subseq(gff, s)
            
            seq[defline] = tmpseq

    return seq
            
def extract_start_end(gff, stype, dline):
    '''Extract seqeuces for a feature only use the Start and End information. The relationship between parent and children would be ignored.'''
    seq=dict()
    roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    if stype == 'pre_trans':
        for root in roots:
            rid = 'NA'
            if root['attributes'].has_key('ID'):
                rid = root['attributes']['ID']
            children = root['children']
            for child in children:
                cid = 'NA'
                if child['attributes'].has_key('ID'):
                    cid = child['attributes']['ID']
                cname = cid
                if child['attributes'].has_key('Name'):
                    cname = child['attributes']['Name']
                defline='>{0:s}'.format(cid)
                if dline == 'complete':
                    defline = '>{0:s}:{1:d}..{2:d}:{3:s}|genomic_sequence({4:s})|Parent={5:s}|ID={6:s}|Name={7:s}'.format(child['seqid'], child['start'], child['end'], child['strand'], child['type'], rid, cid, cname)
                seq[defline] = get_subseq(gff, child)
    elif stype == 'gene':
        for root in roots:
            if root['type'] == 'gene' or root['type'] == 'pseudogene':
                rid = 'NA'
                if root['attributes'].has_key('ID'):
                    rid = root['attributes']['ID']
                rname = rid
                if root['attributes'].has_key('Name'):
                    rname = root['attributes']['ID']
                defline='>{0:s}'.format(rid)
                if dline == 'complete':
                    defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{6:s}|ID={4:s}|Name={5:s}'.format(root['seqid'], root['start'], root['end'], root['strand'], rid, rname, root['type'])
                seq[defline] = get_subseq(gff, root)
    elif stype == 'exon':
        exons = [line for line in gff.lines if line['type'] == 'exon' or line['type'] == 'pseudogenic_exon']
        for exon in exons:
            eid = 'NA'
            if exon['attributes'].has_key('ID'):
                eid = exon['attributes']['ID']
            ename = eid
            if exon['attributes'].has_key('Name'):
                ename = exon['attributes']['Name']
            parents = exon['parents']
            plist = dict()
            for parent in parents:
                for p in parent:
                    plist[p['attributes']['ID']] = 1

            keys = plist.keys()
            pid = ','.join(keys)
            
            defline='>{0:s}'.format(eid)
            if dline == 'complete':
                defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}|Parent={5:s}|ID={6:s}|Name={7:s}'.format(exon['seqid'], exon['start'], exon['end'], exon['strand'], exon['type'], pid, eid, ename)

            seq[defline] = get_subseq(gff, exon)

    return seq
    
def main(gff_file=None, fasta_file=None, stype=None, dline=None, qc=True, output_prefix=None, logger=None):
    if logger == None:
        logger = logging.getLogger(__name__+'stderr')
        logger.setLevel(logging.INFO)
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
        logger.addHandler(stderr_handler)
        logger_null = logging.getLogger(__name__+'null')
        null_handler = logging.NullHandler()
        logger_null.addHandler(null_handler)

    if output_prefix:
        logger.info('Specifying prefix of output file name: (%s)...', output_prefix)
        fname = '{0:s}_{1:s}.fa'.format(output_prefix, stype)
        report_fh = open(fname, 'wb')
    else:
        parser.print_help()
        sys.exit(1)

    if not gff_file or not fasta_file or not stype:
        print('All of Gff file, fasta file, and type of extracted seuqences need to be specified')
        return
    type_set=['gene','exon','pre_trans', 'trans', 'cds', 'pep']
    if not stype in type_set:
        logger.error('Your sequence type is "{0:s}". Sequence type must be one of {1:s}!'.format(stype, str(type_set)))
        return
    logger.info('Reading files: {0:s}, {1:s}...'.format(gff_file, fasta_file))
    gff = Gff3(gff_file=gff_file, fasta_external=fasta_file, logger=logger)

    if qc:
        logger.info('Checking errors...')
        gff.check_parent_boundary()
        gff.check_phase()
        gff.check_reference()
        error_set = function4gff.extract_internal_detected_errors(gff)
        t = intra_model.main(gff, logger=logger)
        if t:
            error_set.extend(t)
        t = single_feature.main(gff, logger=logger)
        if t:
            error_set.extend(t)

        if len(error_set):
            escaped_error = ['Esf0012','Esf0033']
            eSet = list()
            for e in error_set:
                if not e['eCode'] in escaped_error:
                    eSet.append(e)
            if len(eSet):
                logger.warning('The extracted sequences might be wrong for the following features which have formatting errors...')
                print('ID\tError_Code\tError_Tag')
                for e in eSet:
                    tag = '[{0:s}]'.format(e['eTag'])
                    print e['ID'], e['eCode'], tag
    
    logger.info('Extract seqeunces for {0:s}...'.format(stype))
    seq=dict()
    if stype == 'pre_trans' or stype == 'gene' or stype == 'exon':
        seq = extract_start_end(gff, stype, dline)        
    elif stype == 'trans':
        feature_type = ['exon', 'pseudogenic_exon']
        seq = splicer(gff, feature_type,  dline)
    elif stype == 'cds':
        feature_type = ['CDS']
        seq = splicer(gff, feature_type,  dline)
    elif stype == 'pep':
        feature_type = ['CDS']
        tmpseq = splicer(gff, feature_type,  dline)
        for k,v in tmpseq.items():
            k = k.replace("|mRNA(CDS)|", "|peptide|").replace("-RA", "-PA")
            v = translator(v)
            seq[k] = v
            
    if len(seq):
        logger.info('Print out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, stype))
        for k,v in seq.items():
            report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

if __name__ == '__main__':
    logger_stderr = logging.getLogger(__name__+'stderr')
    logger_stderr.setLevel(logging.INFO)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger_stderr.addHandler(stderr_handler)
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)
    import argparse
    from textwrap import dedent
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=dedent("""\
    Extract sequences from specific regions of genome based on gff file.
    Testing enviroment:
    1. Python 2.7

    Inputs:
    1. GFF3: reads from STDIN by default, may specify the file name with the -g argument
    2. fasta file: reads from STDIN by default, may specify the file name with the -f argument

    Outputs:
    1. Extract sequences from specific regions of genome based on gff file.

    """))
    parser.add_argument('-g', '--gff', type=str, help='Genome annotation file in GFF3 format (default: STDIN)') 
    parser.add_argument('-f', '--fasta', type=str, help='Genome sequences in FASTA format (default: STDIN)')
    parser.add_argument('-st', '--sequence_type', type=str, help='Type of seuqences you would like to extract: please select from "gene" - gene sequence for each record; "exon" - exon sequence for each record; "pre_trans" - genomic region of a transcript model (premature transcript); "trans" - spliced transcripts (only exons included); "cds" - coding sequences; "pep" - peptide seuqences.(default: STDIN)')
    parser.add_argument('-d', '--defline', type=str, help='Specify defline format:"simple" - only ID would be shown in the defline; "complete" - complete information of the feature would be shown in the defline.')
    parser.add_argument('-o', '--output_prefix', type=str, help='Prefix of output file name (default: STDIN)')
    parser.add_argument('-noQC', '--quality_control', action='store_false', help='Specify this option if you do not want to excute quality control for gff file. (default: QC is excuted)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    
    args = parser.parse_args()

    if args.gff:
        logger_stderr.info('Checking gff file (%s)...', args.gff)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.fasta:
        logger_stderr.info('Checking genome fasta (%s)...', args.fasta)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.fasta = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.sequence_type:
        logger_stderr.info('Specifying sequence type: (%s)...', args.sequence_type)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.sequence_type = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.defline:
        logger_stderr.info('Defline format: (%s)...', args.defline)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.defline = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)


    main(args.gff, args.fasta, args.sequence_type, args.defline, args.quality_control, args.output_prefix, logger_stderr)
