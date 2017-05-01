#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
# Contributed by Mei-Ju May Chen <arbula [at] gmail [dot] com> (2016)

"""
QC functions for processing multiple features between models (inter-model) in GFF3 file.
"""
from __future__ import print_function

#from collections import OrderedDict # not available in 2.6
from collections import defaultdict
from itertools import groupby
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
from textwrap import wrap
import sys
import re
import logging
import string
import random
logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)
from os.path import dirname
if dirname(__file__) == '':
    lib_path = '../../lib'
else:
    lib_path = dirname(__file__) + '/../../lib'
sys.path.insert(1, lib_path)
from gff3_modified import Gff3

__version__ = '0.0.1'

def randomID(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def FIX_MISSING_ATTR(gff, logger=None): 
    features = [line for line in gff.lines if line['line_type']=='feature']
    flag = 0
    for f in features:
        if not f['attributes'].has_key('owner'):
            f['attributes']['owner'] = 'Unassigned'
        if not f['attributes'].has_key('ID'):
            IDrequired = ['gene', 'pseudogene', 'mRNA', 'pseudogenic_transcript']
            if f['type'] in IDrequired:
                logger.error('[Missing ID] A model needs to have a unique ID, but not. Please fix it before running the program.\n{0:s}'.format(f['line_raw']))
                flag += 1
            else:
                #tid = f['parents'][0][0]['attributes']['ID'] + '-' + f['type']
                tid = randomID()
                while (tid in gff.features):
                    tid = randomID()
                f['attributes']['ID'] = tid
                gff.features[tid].append(f)
    if flag != 0:
        sys.exit()

def featureSort(linelist, reverse=False):
    ''' Used by replace_OGS.py'''
    ''' Used by gff3_to_fasta.py'''
    FEATURECODE = {
        'gene': 0, 
        'pseudogene': 0, 
        'mRNA': 1,
        'rRNA': 1,
        'tRNA': 1,
        'miRNA': 1,
        'snRNA': 1,
        'pseudogenic_transcript': 1,
        'transcript': 1,
        'exon': 2,
        'pseudogenic_exon': 2,
        'CDS': 3,
    }

    id2line = {}
    id2index = {}
    seq2id = {}
    for line in linelist:
        lineindex = line['start'] if reverse==False else line['end']
        id2line[str(line['line_raw'])] = line
        if FEATURECODE.has_key(line['type']):
            id2index[str(line['line_raw'])] = [lineindex, FEATURECODE[line['type']] if reverse==False else (-FEATURECODE[line['type']])]
        else:
            id2index[str(line['line_raw'])] = [lineindex, 99 if reverse==False else -99]
        tmp = re.search('(.+?)(\d+)',line['seqid'])
        seqnum = tmp.groups()[1]
        if seq2id.has_key(seqnum):
            seq2id[seqnum].append(str(line['line_raw']))
        else:
            seq2id[seqnum] = [str(line['line_raw'])]
    keys = sorted(seq2id, key=lambda i: int(i))
    newlinelist=[]
    for k in keys:
        ids = seq2id[k]
        d = {}
        for ID in ids:
            d[ID] = id2index[ID]
        id_sorted = sorted(d, key=lambda i: (int(d[i][0]), int(d[i][1])), reverse=reverse)
        for i in id_sorted:
            newlinelist.append(id2line[i])
    return newlinelist


def extract_internal_detected_errors(gff):
    error_lines = [line for line in gff.lines if line['line_errors']]

    eSet = list()
    for line in error_lines:
        for e in line['line_errors']:
            result = dict()
            result['ID'] = [line['attributes']['ID']]
            result['eCode'] = e['eCode']
            result['eLines'] = [line]
            result['eTag'] = e['message']
            #print('{0:s}\t{1:s}\t[{2:s}]'.format(result['ID'], result['eCode'], result['eTag']))
            eSet.append(result)

    if len(eSet):
        return eSet

