#! /usr/bin/env python2.7

"""
QC functions for processing multiple features between models (inter-model) in GFF3 file.
"""
from __future__ import print_function
import os
import sys
import logging
from gff3tool.lib.utils import remove_files_from_list
from gff3tool.lib.gff3 import Gff3
import gff3tool.lib.ERROR as ERROR
import gff3tool.lib.function4gff as function4gff
import subprocess
logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

ERROR_INFO = ERROR.INFO


def check_duplicate(gff, linelist):
    '''
    This function assumes that,
    1. Each gene is unique
    2. Children features such as Exons/CDSs do not contain multiple Parent IDs

    Note: If there are additional transcript type in the input gff, then you should go to intra_model.featureSort, and add the new transcript type to the dict of FEATURECODE.
    '''

    eCode = 'Emr0001'
    eSet = list()

    pairs = list()
    for i in range(len(linelist)-1):
        for j in range(i+1, len(linelist)):
            source, target = linelist[i], linelist[j]
            if source['seqid'] == target['seqid']:
                s7 = '{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:d}\t{5:s}\t{6:s}\t{7:s}'.format(source['seqid'], source['source'], source['type'], source['start'], source['end'], str(source['score']), source['strand'], str(source['phase']))
                t7 = '{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:d}\t{5:s}\t{6:s}\t{7:s}'.format(target['seqid'], target['source'], target['type'], target['start'], target['end'], str(target['score']), target['strand'], str(target['phase']))
                if s7 == t7:
                    pairs.append({'source':source, 'target':target})

    for pair in pairs:
        result = dict()
        same_target = False
        if pair['source'].has_key('children') and pair['target'].has_key('children'):
            schildren = pair['source']['children']
            tchildren = pair['target']['children']
            if len(schildren) == len(tchildren):
                sort_schildren = function4gff.featureSort(schildren, reverse=True if pair['source']['strand'] == '-' else False)
                sort_tchildren = function4gff.featureSort(tchildren, reverse=True if pair['source']['strand'] == '-' else False)
                for i in range(len(sort_schildren)):
                    s7 = '{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:d}\t{5:s}\t{6:s}\t{7:s}'.format(sort_schildren[i]['seqid'], sort_schildren[i]['source'], sort_schildren[i]['type'], sort_schildren[i]['start'], sort_schildren[i]['end'], str(sort_schildren[i]['score']), sort_schildren[i]['strand'], str(sort_schildren[i]['phase']))
                    t7 = '{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:d}\t{5:s}\t{6:s}\t{7:s}'.format(sort_tchildren[i]['seqid'], sort_tchildren[i]['source'], sort_tchildren[i]['type'], sort_tchildren[i]['start'], sort_tchildren[i]['end'], str(sort_tchildren[i]['score']), sort_tchildren[i]['strand'], str(sort_tchildren[i]['phase']))
                    if s7 == t7:
                        same_target=True
                    else:
                        same_target=False
                        break
        if same_target:
            key = [pair['source']['attributes']['ID'], pair['target']['attributes']['ID']]
            result['ID'] = key
            lnum = ['Line {0:s}'.format(str(pair['source']['line_index']+1)),'Line {0:s}'.format(str(pair['target']['line_index']+1))]
            result['line_num'] = lnum
            result['eCode'] = eCode
            result['eLines'] = [pair['source'], pair['target']]
            result['eTag'] = 'Duplicate transcripts found between {0:s} and {1:s}'.format(pair['source']['attributes']['ID'], pair['target']['attributes']['ID'])
            eSet.append(result)
            gff.add_line_error(pair['source'], {'message': 'Duplicate transcripts found between {0:s} and {1:s}'.format(pair['source']['attributes']['ID'], pair['target']['attributes']['ID']), 'error_type': 'INTER_MODEL', 'eCode': eCode})
            gff.add_line_error(pair['target'], {'message': 'Duplicate transcripts found between {0:s} and {1:s}'.format(pair['source']['attributes']['ID'], pair['target']['attributes']['ID']), 'error_type': 'INTER_MODEL', 'eCode': eCode})

    if len(eSet):
        return eSet

def check_incorrectly_split_genes(gff, gff_file, fasta_file, logger):
    import gff3tool.bin.gff3_to_fasta as gff3_to_fasta
    lib_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
    eCode = 'Emr0002'
    eSet = list()
    gff3_to_fasta.main(gff_file=gff_file, fasta_file=fasta_file, stype='cds', dline='complete', qc=False, output_prefix='tmp', logger=logger)
    cmd = os.path.join(lib_path, 'ncbi-blast+', 'bin', 'makeblastdb')
    logger.info('Making blast database... ({0:s})'.format(cmd))
    subprocess.Popen([cmd, '-in', 'tmp_cds.fa', '-dbtype', 'nucl']).wait()
    cmd = os.path.join(lib_path, 'ncbi-blast+', 'bin', 'blastn')
    logger.info('Aligning sequences... ({0:s})'.format(cmd))
    subprocess.Popen([cmd, '-db', 'tmp_cds.fa', '-query', 'tmp_cds.fa', '-out', 'blastn.out', '-outfmt', '6', '-penalty', '-15', '-ungapped']).wait()
    cmd = os.path.join(lib_path, 'check_gene_parent', 'find_wrongly_split_gene_parent.pl')
    logger.info('Finding mRNAs with wrongly split gene parents... ({0:s})'.format(cmd))
    subprocess.Popen(['perl', cmd, gff_file, 'blastn.out', 'lepdec', 'ck_wrong_split.report']).wait()
    with open('ck_wrong_split.report', 'r') as ck_wrong_split:
        wrongly_split_gene_parent = ck_wrong_split.readlines()
    pairs = list()
    for i in wrongly_split_gene_parent[1:len(wrongly_split_gene_parent)]:
        i = i.strip()
        tokens = i.split('\t')
        source = gff.features[tokens[2]][0]
        target = gff.features[tokens[3]][0]
        pairs.append({'source':source, 'target':target})

    for pair in pairs:
        result = dict()
        key = [pair['source']['attributes']['ID'], pair['target']['attributes']['ID']]
        result['ID'] = key
        lnum = ['Line {0:s}'.format(str(pair['source']['line_index']+1)),'Line {0:s}'.format(str(pair['target']['line_index']+1))]
        result['line_num'] = lnum
        result['eCode'] = eCode
        result['eLines'] = [pair['source'], pair['target']]
        result['eTag'] = ERROR_INFO[eCode]
        eSet.append(result)
        gff.add_line_error(pair['source'], {'message': '{0:s} between {1:s} and {2:s}'.format(ERROR_INFO[eCode], pair['source']['attributes']['ID'], pair['target']['attributes']['ID']), 'error_type': 'INTER_MODEL', 'eCode': eCode})
        gff.add_line_error(pair['target'], {'message': '{0:s} between {1:s} and {2:s}'.format(ERROR_INFO[eCode], pair['source']['attributes']['ID'], pair['target']['attributes']['ID']), 'error_type': 'INTER_MODEL', 'eCode': eCode})

    logger.info('Removing unnecessary files...')
    rm_list = ['tmp_cds.fa', 'tmp_cds.fa.nhr', 'tmp_cds.fa.nin', 'tmp_cds.fa.nsq', 'blastn.out', 'GeneModelwithMultipleIsoforms.txt','ck_wrong_split.report']
    remove_files_from_list(rm_list)

    if len(eSet):
        return eSet


def main(gff, gff_file, fasta_file, logger=None, noncanonical_gene = False):
    function4gff.FIX_MISSING_ATTR(gff, logger=logger)
    roots = []
    for line in gff.lines:
        try:
            if line['line_type']=='feature' and not line['attributes'].has_key('Parent'):
                roots.append(line)
        except:
            logger.warning('[Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))

    #roots = [line for line in gff.lines if line['line_type']=='feature' and not line['attributes'].has_key('Parent')]
    error_set=list()
    trans_list = list()
    for root in roots:
        children = root['children']
        for child in children:
            trans_list.append(child)
    r = None
    if noncanonical_gene == False:
        r = check_duplicate(gff, trans_list)
    if r is not None:
        error_set.extend(r)
    r = None
    if noncanonical_gene == False:
        r = check_incorrectly_split_genes(gff, gff_file, fasta_file, logger)
    if r is not None:
        error_set.extend(r)
    r = None

    '''
    for e in error_set:
        tag = '[{0:s}]'.format(ERROR_INFO[e['eCode']])
        print(e['ID'], e['eCode'], tag)
    '''

    if len(error_set):
        return(error_set)