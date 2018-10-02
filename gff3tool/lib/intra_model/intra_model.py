#! /usr/bin/env python2.7

"""
QC functions for processing multiple features within a model (intra-model) in GFF3 file.
"""
from __future__ import print_function
import sys
import re
import logging
import gff3tool.lib.function4gff as function4gff
import gff3tool.lib.ERROR as ERROR


logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

ERROR_INFO = ERROR.INFO

def check_redundant_length(gff, rootline):
    eCode = 'Ema0001'
    result = dict()

    flag = 0
    gene_start = rootline['start']
    gene_end = rootline['end']
    try:
        gene_len = gene_end - gene_start + 1
    except:
        gff.add_line_error(rootline, {'message': ERROR_INFO['Esf0017'], 'error_type': 'FEATURE_TYPE', 'eCode':'Esf0017'})
        gene_len = 0
    children = rootline['children']
    c_start = list()
    c_end = list()
    for child in children:
        c_start.append(child['start'])
        c_end.append(child['end'])
    if len(c_start) > 0 and len(c_end) > 0:
        min_start = min(c_start)
        max_end = max(c_end)
        try:
            child_len = max_end - min_start + 1
        except:
            child_len = 0
        #print(min_start, c_start, max_end, c_end)


        if ((min_start != gene_start or max_end != gene_end) and (gene_len > child_len)):
            result['eLines']=list()
            result['ID'] = [rootline['attributes']['ID']]
            result['line_num'] = ['Line {0:s}'.format(str(rootline['line_index'] + 1))]
            result['eCode'] = eCode
            for child in children:
                result['eLines'].append(child)
            result['eTag'] = ERROR_INFO[eCode]
            flag += 1

    if flag > 0:
        gff.add_line_error(rootline, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    if len(result):
        return [result]

def check_internal_stop(gff, rootline):
    import gff3tool.bin.gff3_to_fasta as gff3_to_fasta # TODO: mutual import, should be avoided
    eCode = 'Ema0002'
    result = list()

    children = rootline['children']
    for child in children:
        r = dict()
        flag = 0
        segments = []
        gchildren = child['children']
        for gchild in gchildren:
            if gchild['type'] == 'CDS':
                segments.append(gchild)

        sort_seg = function4gff.featureSort(segments)
        try:
            if gchild['strand'] == '-':
                sort_seg = function4gff.featureSort(segments, reverse=True)
        except:
            pass
            #logger.warning('[Attributes Format error] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(rootline['line_index']+1), rootline['line_raw']))
        tmpseq = ''
        tmpindex = list()
        count = 0
        for s in sort_seg:
            if count == 0:
                start, end = int, int
                line = s
                if line['type'] == 'CDS':
                    if not isinstance(line['phase'], int):
                        #gff.add_line_error(line, {'message': '{0:s} {1:s}, should be 0,1, or 2'.format(ERROR_INFO['Ema0006'], line['phase']), 'error_type': 'PHASE', 'eCode': 'Ema0006'})
                        continue
                        #sys.exit('[Error] No phase informatin!\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                    try:
                        start = line['start']+line['phase']
                    except:
                        pass
                    end = line['end']
                    if line['strand'] == '-':
                        start = line['start']
                        try:
                            end = line['end']-line['phase']
                        except:
                            pass
                else:
                    start = line['start']
                    end = line['end']

                s['start'] = start
                s['end'] = end
                s['phase'] = 0
            tmpseq = tmpseq + gff3_to_fasta.get_subseq(gff, s)
            try:
                index = list(range(s['start']+s['phase'], s['end']+1, 3))
            except:
                sys.exit('[Error] Start/End is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
            if line['strand'] == '-':
                try:
                    index = list(range(s['end']-s['phase'], s['start']-1, -3))
                except:
                    sys.exit('[Error] Start/End is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
            tmpindex.extend(index)
            #print(s['start'], s['end'], s['phase'])
            count += 1
        aa = gff3_to_fasta.translator(tmpseq)
        stop = [m.start() for m in re.finditer('\*', aa)]
        bp = list()
        for i in stop:
            if i < len(aa)-1:
                bp.append(str(tmpindex[i]))


        if len(bp):
#            print(tmpindex, len(tmpindex), tmpseq, len(tmpseq), aa, len(aa), stop, bp)
 #           print(' ,and '.join(bp))
            r['ID'] = [child['attributes']['ID']]
            r['line_num'] = ['Line {0:s}'.format(str(child['line_index'] + 1))]
            r['eCode'] = eCode
            r['eLines']=list()
            r['eLines'].append(child)
            r['eTag'] = '{0:s} at bp {1:s}'.format(ERROR_INFO[eCode], ', and '.join(bp))
            flag += 1

        if flag > 0:
            result.append(r)
            gff.add_line_error(rootline, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})

    if len(result):
        return result


def check_incomplete(gff, rootline):
    eCode = 'Ema0004'
    result = dict()

    flag = 0
    if rootline['type'] == 'gene':
        children = rootline['children']
        mRNA = 0
        eflag = 0
        for child in children:
            if child['type'] == 'mRNA':
                mRNA += 1
                gchildren = child['children']
                exon = 0
                cds = 0
                for gchild in gchildren:
                    if gchild['type'] == 'exon':
                        exon += 1
                    elif gchild['type'] == 'CDS':
                        cds += 1
                if exon==0 or cds ==0:
                    eflag += 1

        if mRNA == 0:
            eflag += 1

        if eflag > 0:
            result['ID'] = [rootline['attributes']['ID']]
            result['line_num'] = ['Line {0:s}'.format(str(rootline['line_index'] + 1))]
            result['eCode'] = eCode
            result['eLines']=list()
            result['eLines'].append(rootline)
            result['eTag'] = ERROR_INFO[eCode]
            flag += 1

    if flag > 0:
        gff.add_line_error(rootline, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})

    if len(result):
        return [result]




def check_pseudo_child_type(gff, rootline):
    eCode = 'Ema0005'
    result = dict()

    if rootline['type'] == 'pseudogene':
        children = rootline['children']
        flag = 0
        for child in children:
            if child['type'] == 'transcript' or child['type'] == 'pseudogenic_transcript':
                pass
            else:
                flag += 1
                if len(result):
                    result['eLines'].append(child)
                else:
                    result['ID'] = [rootline['attributes']['ID']]
                    result['line_num'] = ['Line {0:s}'.format(str(rootline['line_index'] + 1))]
                    result['eCode'] = eCode
                    result['eLines'] = [child]
                    result['eTag'] = ERROR_INFO[eCode]
        if flag > 0:
            gff.add_line_error(rootline, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    if len(result):
        return [result]

def check_distinct_isoform(gff, rootline):
    '''
    Detect models with distant isoforms
    * workflow:
      (a) For each gene/pseudogene model, compare the regions (start and end) of all isoforms (n);
          (i) For each isoforms, a flag (all) to record all possible comparison (one isoform has n comparison), and the other flag (hit) to accumulate overlapped isoforms.
              * record models 'without' the condition of hit == 1 (self overlapping)
              * record panelty by counting how may isoforms with the condition of hit == all (the isoform is overlapped with all other isoforms)
          (ii) Report the model that:
               * is NOT all isofroms are with the condition hit == all
               * does NOT contain isoforms with the condition of hit == 1
    * Example:
      (Example a) a model with three isoforms (x, y, z)
          for isoform x, all=3 (x-x, x-y, x-z) and the possible conditions of hit are 3(1,1,1), 2(1,0,1), 2(1,1,0), 1(1,0,0). If hit=all (3 in this example) or hit=1, then the model would be ignored. Otherwise, the model would be recorded as models with distant isoforms.
      (Example b) a model with 2 isoforms (x, y)
          for isoform x, all=2 (x-x, x-y) and the possible conditions of hit are 2(1,1), 1(1,0). The conditions would always be hit=all (2 in this example) or hit=1, so cases like this example would never be reported in this category.
'''

    eCode = 'Ema0008'
    result = dict()

    children = rootline['children']
    flag = 0
    panelty = 0
    badchild = []
    bclist = []
    f = 0
    for child1 in children:
        allcombination = 0
        hit = 0
        for child2 in children:
            allcombination += 1
            if gff.overlap(child1, child2):
                hit += 1
        if hit==allcombination:
            panelty += 1
        if hit < allcombination:
            badchild.append(child1['attributes']['ID'])
            bclist.append(child1)
        if hit==1:
            continue
        flag += 1

    if panelty == len(children):
        flag -= 1
    if flag == len(children):
        f += 1
        result['eLines']=list()
        result['eLines'].extend(bclist)
        result['ID'] = [rootline['attributes']['ID']]
        result['line_num'] = ['Line {0:s}'.format(str(rootline['line_index'] + 1))]
        result['eCode'] = eCode
        result['eTag'] = '{0:s}: {1:s}'.format(ERROR_INFO[eCode], str(badchild))

    if f > 0:
        gff.add_line_error(rootline, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    if len(result):
        return [result]

def check_merged_gene_parent(gff, rootline):
    eCode = 'Ema0009'
    result = dict()
    f=0
    badchild = dict()
    children = rootline['children']
    if len(children) > 1:
        hit = 0
        for idx, child1 in enumerate(children[:-1]):
            gchildren1 = child1['children']
            for child2 in children[idx+1:]:
                gchildren2 = child2['children']
                for gchild1 in gchildren1:
                    for gchild2 in gchildren2:
                        if gchild1['type'] == 'CDS' and gchild2['type'] == 'CDS':
                            if gff.overlap(gchild1, gchild2):
                                hit += 1
            if hit == 0:
                pair = sorted([child1['line_index'] + 1, child2['line_index'] + 1])
                badchild[str(pair)] = 1

        if hit == 0:
            f += 1
            result['eLines']=list()
            result['ID'] = [rootline['attributes']['ID']]
            result['line_num'] = ['Line {0:s}'.format(str(rootline['line_index'] + 1))]
            result['eCode'] = eCode
            result['eTag'] = '{0:s}: Between Line {1:s}'.format(ERROR_INFO[eCode], ', and Line'.join(badchild))
    if f > 0:
        gff.add_line_error(rootline, {'message': ERROR_INFO[eCode], 'error_type': 'FEATURE_TYPE', 'eCode': eCode})
    if len(result):
        return [result]


def main(gff, logger=None, noncanonical_gene=False):
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
    for root in roots:
        r = check_pseudo_child_type(gff, root)
        if not r == None:
            error_set.extend(r)
        r = None
        r = check_redundant_length(gff, root)
        if not r == None:
            error_set.extend(r)
        r = None
        if noncanonical_gene == False:
            r = check_incomplete(gff, root)
        if not r == None:
            error_set.extend(r)
        r = None
        if noncanonical_gene == False:
            r = check_internal_stop(gff, root)
        if not r == None:
            error_set.extend(r)
        r = None
        if noncanonical_gene == False:
            r = check_distinct_isoform(gff, root)
        if not r == None:
            error_set.extend(r)
        r = None
        if noncanonical_gene == False:
            r = check_merged_gene_parent(gff, root)
        if not r == None:
            error_set.extend(r)
        r = None

#    for e in error_set:
#        print('{3:s}\t{0:s}\t{1:s}\t{2:s}\n'.format(e['ID'], e['eCode'], e['eTag'], e['line_num']))

    if len(error_set):
        return(error_set)
