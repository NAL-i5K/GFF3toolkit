#! /usr/local/bin/python2.7
# Copyright (C) 2015  Mei-Ju Chen <arbula [at] gmail [dot] com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""
Changelog:
    * v0.0.2
        - Sort the features grouped as 'others' by PositionSort
        - Add comments
"""

import sys
import re
import logging
# try to import from project first
from os.path import dirname
if dirname(__file__) == '':
    bin_path = '../lib'
else:
    bin_path = dirname(__file__) + '/../lib'
sys.path.insert(1, bin_path)
from gff3_modified import Gff3
import version

__version__ = version.__version__


def PositionSort(linelist):
    # the input argument, 'linelist', is a python list collecting all the features you would like to sort by genomic coordinates
    id2line = {}
    id2start = {}
    seq2id = {}
    for line in linelist:
        id2line[str(line['line_raw'])] = line
        id2start[str(line['line_raw'])] = (line['start'],line['line_index'])
        tmp = re.search('(.+?)(\d+)',line['seqid']) # Truncate the sequence ID, and only keep the sequence ID number
        try:
            seqnum = tmp.groups()[1]
        except:
            print('ERROR  [Missing SeqID] Missing SeqID.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1),line['line_raw']))
            sys.exit(1)
        # 'seq2id': a dictionary mapping sequence number to their features
        if seq2id.has_key(seqnum):
            seq2id[seqnum].append(str(line['line_raw']))
        else:
            seq2id[seqnum] = [str(line['line_raw'])]
    # Sort by sequence ID number, and store them in 'keys'
    keys = sorted(seq2id, key=lambda i: int(i))
    newlinelist=[]
    # Visit every sequence number in the sorted list
    for k in keys:
        ids = seq2id[k] # Collect features having the same sequence ID number
        d = {}
        for ID in ids:
            d[ID] = id2start[ID][0] # Collect the 'start' coordinate of each feature with the same seqeunce ID number
            try:
                int(d[ID])
            except:
                print('ERROR [Start] Start is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(id2start[ID][1]+1),ID))
                sys.exit(1)

        id_sorted = sorted(d, key=lambda i: int(d[i])) # Sort the features by their 'start' coordinates
        for i in id_sorted:
            newlinelist.append(id2line[i]) # Collect the sorted features to the result parameter
    return newlinelist # Return the sorted result

def StrandSort(linelist):
    # the input argument, 'linelist', is a python list collecting features with the same strand information and the same type! Please note that linelist has to be single feature type, eg. exon.
    strand = {}
    seq = {}
    id2line = {}
    id2start = {}
    id2end = {}
    for line in linelist:
        #print(line['attributes']['ID']) # debug
        strand[line['strand']] = 0
        seq[line['seqid']] = 0
        id2line[str(line['line_raw'])] = line
        id2start[str(line['line_raw'])] = (line['start'],line['line_index'])
        id2end[str(line['line_raw'])] = (line['end'],line['line_index'])

    # Required conditions for the input line list
    if not len(seq) == 1:
        print('Not all lines located in the same sequence. Cannot process by StrandSort.')
        return
    if not len(strand) == 1:
        print('Strand is not consistent among all lines in the list or strand information is missing. Cannot process by StrandSort.')
        return

    # Sort by ascending order of genomic coordinates if the stran is '+', and by descending order if '-'. If the strand information is unclear, report error.
    newlinelist=[]
    for k in strand:
        if k == '+':
            try:
                id_sorted = sorted(id2start, key=lambda i: int(id2start[i][0]))
                for i in id_sorted:
                    newlinelist.append(id2line[i])
            except:
                for i in id2start:
                    try:
                        int(id2start[i][0])
                    except:
                        print('ERROR  [Start] Start is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(id2start[i][1]+1),i))
                        sys.exit(1)
        elif k == '-':
            try:
                id_sorted = sorted(id2end, key=lambda i: int(id2end[i][0]), reverse=True)
                for i in id_sorted:
                    newlinelist.append(id2line[i])
            except:
                for i in id2end:
                    try:
                        int(id2end[i][0])
                    except:
                        print('ERROR  [End] End is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(id2end[i][1]+1),i))
                        sys.exit(1)
        else:
            print('[Error]\tStrand is not clear. Cannot process by StrandSort.')
    return newlinelist
def TwoParent(Child_id,third):
    #the input argument, Child_id is the id of second-level features (eg. mRNA, ncRNA, and etc.) and third is third-level features (eg. exon, CDS, and etc.)
    attributes = third['attributes'].copy()
    attributes['Parent'] = Child_id
    attributes_line = ";".join("=".join((str(k),str(v))) for k,v in attributes.iteritems())
    line_new = third['line_raw'].split('\t')
    line_new[8] = attributes_line + "\n"
    line_update = "\t".join(line_new)

    return line_update

def main(gff, output=None, logger=None):
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    gff3 = Gff3(gff_file=gff, logger=logger_null)

    if output:
        report = open(output, 'wb')
    else:
        report = sys.stdout


    logger.info('Sorting and printing out...')
    
    # Visit the GFF3 object through root-level features (eg. gene, pseudogene, and etc.)
    roots =[]
    gff3_linenum_Set = set()
   
    for line in gff3.lines:
       if line['line_type'] == 'feature':
           gff3_linenum_Set.add(line['line_index'])
       try:
           if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent') and len(line['attributes']) != 0:
               roots.append(line)
       except:
           logger.warning('[Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
    #roots = [line for line in gff3.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]

    # Sort the root-level features based on the order of the genomic sequences
    roots_sorted = PositionSort(roots)

    # Write the gff version
    # report.write('##gff-version 3\n')

    wrote_sequence_region = set()
    # build sequence region data
    sequence_regions = {}
    if gff3.fasta_embedded:
        for seqid in gff3.fasta_embedded:
            sequence_regions[seqid] = (1, len(gff3.fasta_embedded[seqid]['seq']))
    else:
        directives_lines = [line_data for line_data in gff3.lines if line_data['line_type'] == 'directive' and line_data['directive'] == '##sequence-region']
        for sequence_region in directives_lines:
            sequence_regions[sequence_region['seqid']] = (sequence_region['start'], sequence_region['end'])
    ignore_directives = ['##sequence-region', '###', '##FASTA']
    # write directive
    directives_lines = [line_data for line_data in gff3.lines if line_data['line_type'] == 'directive' and line_data['directive'] not in ignore_directives]
    for directives_line in directives_lines:
        report.write(directives_line['line_raw'])
    
    # Visit every root-level feature
    for root in roots_sorted:
        # write ##sequence-region
        if root['seqid'] not in wrote_sequence_region:
            if root['seqid'] in sequence_regions:
                report.write('##sequence-region %s %d %d\n' % (root['seqid'], sequence_regions[root['seqid']][0], sequence_regions[root['seqid']][1]))
            wrote_sequence_region.add(root['seqid'])

        report.write(root['line_raw'])
        gff3_linenum_Set.discard(root['line_index'])
        children = root['children'] # Collect the second-level features (eg. mRNA, ncRNA, and etc.)
        children_sorted = PositionSort(children)
        otherlines=[]
        for child in children_sorted:
            ## ID information is stored in child['attributes']['ID']
            #print('----------------')
            gff3_linenum_Set.discard(child['line_index'])
            report.write(child['line_raw'])
            grandchildren = child['children'] # Collect third-level features (eg. exon, CDS, and etc.)
            gchildgroup = {}
            # Visit every third-level feature, and collect a dictionary of 'type' to 'features'
            for grandchild in grandchildren: # Visit each third-level feature
                if gchildgroup.has_key(str(grandchild['type'])):
                    gchildgroup[str(grandchild['type'])].append(grandchild)
                else:
                    gchildgroup[str(grandchild['type'])] = []
                    gchildgroup[str(grandchild['type'])].append(grandchild)
                otherlines.extend(gff3.collect_descendants(grandchild))
            # Seperate the third-level features into three groups: exon, cds, and others
            exons = []
            cdss = []
            others = []
            for k, v in gchildgroup.items():
                if k == 'exon' or k == 'pseudogenic_exon':
                    exons.extend(v)
                elif k == 'CDS':
                    cdss.extend(v)
                else:
                    others.extend(v)

            # Sort exons by considering strand information (StrandSort)
            if len(exons):
                exons_sorted = []
                if StrandSort(exons):
                    exons_sorted = StrandSort(exons)
                    for exon in exons_sorted:
                        if exon['attributes'].has_key('Parent'):
                            if isinstance(exon['attributes']['Parent'], list) and len(exon['attributes']['Parent']) > 1:
                                gff3_linenum_Set.discard(exon['line_index'])
                                report.write(TwoParent(child['attributes']['ID'],exon))
                            else:
                                gff3_linenum_Set.discard(exon['line_index'])
                                report.write(exon['line_raw'])
                        else:
                            gff3_linenum_Set.discard(exon['line_index'])
                            report.write(exon['line_raw'])
            # Sort cds features by considering strand information (StrandSort)
            if len(cdss):
                cdss_sorted = []
                if StrandSort(cdss):
                    cdss_sorted = StrandSort(cdss)
                    for cds in cdss_sorted:
                        if cds['attributes'].has_key('Parent'):
                            if isinstance(cds['attributes']['Parent'], list) and len(cds['attributes']['Parent']) > 1:
                                gff3_linenum_Set.discard(cds['line_index'])
                                report.write(TwoParent(child['attributes']['ID'],cds))
                            else:
                                gff3_linenum_Set.discard(cds['line_index'])
                                report.write(cds['line_raw'])
                        else:
                            gff3_linenum_Set.discard(cds['line_index'])            
                            report.write(cds['line_raw'])
            # Sort other features by PositionSort
            if len(others):
                if PositionSort(others):
                    for other in others:
                        if other['attributes'].has_key('Parent'):
                            if type(other['attributes']['Parent']) == type([]) and len(other['attributes']['Parent']) > 1:
                                gff3_linenum_Set.discard(other['line_index'])
                                report.write(TwoParent(child['attributes']['ID'],other))
                            else:
                                gff3_linenum_Set.discard(other['line_index'])
                                report.write(other['line_raw'])
                        else:
                            gff3_linenum_Set.discard(other['line_index'])
                            report.write(other['line_raw'])

        # Sort the features beyond the third-level by PositionSort
        unique = {}
        otherlines_sorted = []
        if PositionSort(otherlines):
            otherlines_sorted = PositionSort(otherlines)
        for k in otherlines_sorted:
            gff3_linenum_Set.discard(k['line_index'])
            unique[k['line_raw']] = 1
        for k,v in unique.items():
            report.write(k)
        report.write('###\n')
    #Missing 'root' feature
    if len(gff3_linenum_Set) !=0:
        logger.warning('The following lines are omitted from the output file, because there is a problem with the input file. Please review the input file or run gff-QC.py to identify the error.\n')
        for line_num in gff3_linenum_Set:
            print('\t\t- Line {0:s}: {1:s}'.format(str(line_num+1), gff3.lines[line_num]['line_raw']))

    # write fasta
    fasta = gff3.fasta_embedded
    if fasta != False:
        report.write('##FASTA\n')
        for key in fasta:
            seq = fasta[key]['seq']
            report.write(u'{0:s}\n{1:s}\n'.format(fasta[key]['header'],seq))
        
     

if __name__ == '__main__':
    # Set up logger information
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
    # Help information
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=dedent("""\
    Sort a GFF3 file according to the order of Scaffold, coordinates on a Scaffold, and feature relationship based on sequence ontology.

    Inputs:
    1. GFF3 file: Specify the file name with the -g argument

    Outputs:
    1. Sorted GFF3 file: Specify the file name with the -og argument

    Examples:
    1. Specify the input, output file names and options using short arguments:
       python2.7 %(prog)s -g example_file/example.gff3 -og example_file/example_sorted.gff
    2. Specify the input, output file names and options using long arguments:
       python2.7 %(prog)s --gff_file example_file/example.gff3 --output_gff example_file/example_sorted.gff

    """))
    parser.add_argument('-g', '--gff_file', type=str, help='GFF3 file that you would like to sort.')
    parser.add_argument('-og', '--output_gff', type=str, help='Sorted GFF3 file')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    
    # Process the required arguments
    test_lv = 1 # debug
    if test_lv == 0:
        args = parser.parse_args(['-g', 'annotations.gff'])
    else:
        args = parser.parse_args()

    if args.gff_file:
        logger_stderr.info('Checking GFF3 file (%s)...', args.gff_file)
    else: # no input
        parser.print_help()
        sys.exit(1)

    # Creat GFF3 object
    logger_stderr.info('Reading gff3 file...')
    main(args.gff_file, output=args.output_gff, logger=logger_stderr)

