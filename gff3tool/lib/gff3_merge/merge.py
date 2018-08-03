#! /usr/bin/env python2.7
"""
Replace predicted models with Web Apollo models accoriding to attribute, relace=
"""

import sys
import re
import logging
from gff3tool.lib import replace_OGS
from gff3tool.lib.gff3 import Gff3
from gff3tool.lib.utils import remove_files_from_list
import gff3tool.bin.gff3_sort as gff3_sort


def main(gff_file1, gff_file2, output_gff, report_fh, user_defined1=None, user_defined2=None, logger=None):
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    if not logger:
        logger = logger_null
    logger.info('Sorting the WA gff by following the order of Scaffold number and coordinates...')
    gff3_sort.main(gff_file1, output='WA_sorted.gff', logger=logger)

    logger.info('Sorting the other gff by following the order of Scaffold number and coordinates...')
    gff3_sort.main(gff_file2, output='other_sorted.gff', logger=logger)

    logger.info('Reading WA gff3 file...')
    gff3 = Gff3(gff_file='WA_sorted.gff', logger=logger_null)

    logger.info('Reading the other gff3 file...')
    gff3M = Gff3(gff_file='other_sorted.gff', logger=logger_null) #Maker

    logger.info('Identifying types of replacement based on replace tag...')
    ReplaceGroups = replace_OGS.Groups(WAgff=gff3, Pgff=gff3M, outsideNum=1, user_defined1=user_defined1, user_defined2=user_defined2, logger=logger_null)

    logger.info('Replacing...')
    u_types = set()
    u1_types = set()
    if user_defined1 is not None:
        for line in user_defined1:
            u1_types.add(line[0])
        u_types |= u1_types
    else:
        u1_types = None
    u2_types = set()
    if user_defined2 is not None:
        for line in user_defined2:
            u2_types.add(line[0])
        u_types |= u2_types
    else:
        u2_types = None
    roots = []
    transcripts = []
    unique = set()
    for line in gff3.lines:

        if user_defined1 is None:
            try:
                if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                    roots.append(line)
            except:
                pass
        else:
            if line['type'] in u1_types:
                transcripts.append(line)
                for root in gff3.collect_roots(line):
                    if root['line_raw'] not in unique:
                        roots.append(root)
                        unique.add(root['line_raw'])

    #roots = [line for line in gff3.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    rnum, cnum, changed = 0, 0, 0
    cal_type_children = {}
    changed_rootid = set()
    not_orphan = set()
    for root in roots:
        rnum += 1
        if user_defined1 is None:
            children = root['children']
        else:
            children = []
            unique = set()
            if root['type'] in u1_types:
                children.append(root)
            else:
                for child in gff3.collect_descendants(root):
                    if child['type'] in u1_types:
                        if child['line_raw'] not in unique:
                            children.append(child)
                            unique.add(child['line_raw'])
            children = sorted(children, key=lambda k: k['line_index'])

        tags = {}
        cnum += len(children)
        maxisoforms = 0
        for child in children:
            tags[str(child['attributes']['replace'])] = 0
            for tag in child['attributes']['replace']:
                if not tag == 'NA':
                    not_orphan.add(tag)
                    t = gff3M.features[ReplaceGroups.mapName2ID[tag]][0]
                    if user_defined2 is None:
                        tmp = len(t['parents'][0][0]['children'])
                    else:
                        if len(t['parents']) == 0 and t['type'] in u2_types:
                            #this transcript don't have parent feature(e.g. gene), set the number of isoform as 1.
                            tmp = 1
                        else:
                            tmp = len(t['parents'][0][0]['children'])


                    if tmp > maxisoforms:
                        maxisoforms = tmp
        if len(tags) <= 1:
            if maxisoforms >= 2:
                root['attributes']['replace_type'] = 'multi-ref'
                for child in children:
                    child['attributes']['replace_type'] = 'multi-ref'
                if user_defined1 is None:
                    ans = ReplaceGroups.replacer_multi(root, ReplaceGroups, gff3M, u1_types, u2_types)
                else:
                    ans = ReplaceGroups.replacer_multi(root, ReplaceGroups, gff3M, u1_types, u2_types, gff3)
                report_fh.write('{0:s}\n'.format(ans))
                changed_rootid.add(root['attributes']['ID'])
                changed += 1
            else:
                ReplaceGroups.replacer(root, ReplaceGroups, gff3M, u1_types, gff3)
                changed_rootid.add(root['attributes']['ID'])
                changed += 1
        else:
            logger.info('[Warning] multiple replace tags in multiple isoforms! {0:s}. This model is not processed\n'.format(root['attributes']['ID']))
            report_fh.write('[Warning] multiple replace tags in multiple isoforms! {0:s}. This model is not processed\n'.format(root['attributes']['ID']))
        for child in children:
            if child['attributes'].has_key('status') and (child['attributes']['status'] == 'Delete' or child['attributes']['status'] == 'delete'):
                child['attributes']['replace_type'] = 'Delete'
            if cal_type_children.has_key(child['attributes']['replace_type']):
                cal_type_children[child['attributes']['replace_type']] += 1
            else:
                cal_type_children[child['attributes']['replace_type']] = 1

    cal_type = {}
    for i in ReplaceGroups.info:
        tokens = i.split('\t')
        tmp = re.search('(.+?):(.*)', tokens[3])
        if cal_type.has_key(tmp.groups()[0]):
            cal_type[tmp.groups()[0]] += 1
        else:
            cal_type[tmp.groups()[0]] = 1
        #print('{0:s}'.format(i))

    report_fh.write('# Number of WA loci: {0:d}\n'.format(rnum))
    report_fh.write('# Number of WA transcripts: {0:d}\n'.format(cnum))
    report_fh.write('# Number of WA loci that were used to replace the models in reference gff: {0:d}\n'.format(changed))

    for k, v in cal_type.items():
        if k == 'simple':
            report_fh.write('# Number of loci with {0:s}/Delete replacement: {1:d}\n'.format(k, v) )
        else:
            report_fh.write('# Number of loci with {0:s} replacement: {1:d}\n'.format(k, v) )
    for k, v in cal_type_children.items():
        report_fh.write('# Number of transcripts with {0:s} replacement: {1:d}\n'.format(k, v) )

    report_fh.write('Change_log\tOriginal_gene_name\tOriginal_transcript_ID\tOriginal_transcript_name\tTmp_OGSv0_ID\n')

    roots = []
    transcripts = []
    unique = set()
    for line in gff3M.lines:
        if user_defined2 is None:
            try:
                if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                    roots.append(line)
            except:
                pass
        else:
            if line['type'] in u_types:
                transcripts.append(line)
                for root in gff3M.collect_roots(line):
                    if root['line_raw'] not in unique:
                        roots.append(root)
                        unique.add(root['line_raw'])

    #roots = [line for line in gff3M.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    for root in roots:
        if root['attributes']['ID'] not in changed_rootid:
            if user_defined2 is None:
                children = root['children']

            else:
                children = []
                unique = set()
                if root['type'] in u_types:
                    children.append(root)
                else:
                    for child in gff3M.collect_descendants(root):
                        if child['type'] in u_types:
                            if child['line_raw'] not in unique:
                                children.append(child)
                                unique.add(child['line_raw'])
                children = sorted(children, key=lambda k: k['line_index'])
        elif root['attributes']['ID'] in changed_rootid and user_defined1 is not None:
            children = []
            unique = set()
            if root['type'] in u1_types:
                children.append(root)
            else:
                for child in gff3.collect_descendants(root):
                    if child['type'] in u1_types:
                        if child['line_raw'] not in unique:
                            children.append(child)
                            unique.add(child['line_raw'])
            children = sorted(children, key=lambda k: k['line_index'])
        else:
            children = root['children']


        for child in children:
            cflag = 0
            if not child['line_status'] == 'removed':
                #print(child['attributes'])
                if child['attributes'].has_key('replace_type'):
                    for i in root['attributes']['replace']:
                        tname, tid, gid, tmpid = 'NA', 'NA', 'NA', 'NA'
                        tmpid = child['attributes']['ID']
                        if not i == 'NA':
                            t = gff3M.features[ReplaceGroups.mapName2ID[i]][0]
                            try:
                                tname = t['attributes']['Name']
                            except:
                                tname = t['attributes']['ID']
                            tid = t['attributes']['ID']
                            gid_list = list()
                            if user_defined2 is None:
                                for tp_line in t['parents']:
                                    for tp in tp_line:
                                        gid_list.append(tp['attributes']['ID'])
                                gid = ','.join(gid_list)
                            else:
                                for tp in gff3M.collect_roots(t):
                                    gid_list.append(tp['attributes']['ID'])
                                gid = ','.join(gid_list)
                            if tname not in not_orphan:
                                tmpid = 'NA'
                        report_fh.write('{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n'.format(ReplaceGroups.mapType2Log[child['attributes']['replace_type']], gid, tid, tname, tmpid))
                    del child['attributes']['replace_type']
                    cflag += 1
                if child['attributes'].has_key('replace'):
                    del child['attributes']['replace']
                if cflag == 0:
                    gid = None
                    gid_list = list()
                    if user_defined2 is None:
                        for p_line in child['parents']:
                            for p in p_line:
                                gid_list.append(p['attributes']['ID'])
                    else:
                        for p in gff3M.collect_roots(child):
                            gid_list.append(p['attributes']['ID'])

                    gid = ','.join(gid_list)
                    report_fh.write('{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n'.format(ReplaceGroups.mapType2Log['other'], gid, child['attributes']['ID'], ReplaceGroups.id2name[child['attributes']['ID']], child['attributes']['ID']))
            else:
                if child['attributes'].has_key('status') and child['attributes']['status'] == 'Delete':
                    for i in child['attributes']['replace']:
                        if i == 'NA':
                            sys.exit('The replace tag for Delete replacement cannot be NA: {0:s}'.format(child['line_raw']))
                        t = gff3M.features[ReplaceGroups.mapName2ID[i]][0]
                        tname = t['attributes']['Name']
                        tid = t['attributes']['ID']
                        gid_list = list()
                        if user_defined2 is None:
                            for tp_line in t['parents']:
                                for tp in tp_line:
                                    gid_list.append(tp['attributes']['ID'])
                        else:
                            for tp_line in gff3M.collect_roots(t):
                                gid_list.append(tp_line['attributes']['ID'])

                        gid = ','.join(gid_list)

                        report_fh.write('{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n'.format(ReplaceGroups.mapType2Log['Delete'], gid, tid, tname, "NA"))
                    if child['attributes'].has_key('replace'):
                        del child['attributes']['replace']


        if root['attributes'].has_key('replace'):
            del root['attributes']['replace']
        if root['attributes'].has_key('replace_type'):
            del root['attributes']['replace_type']
        if root['attributes'].has_key('modified_track'):
            del root['attributes']['modified_track']

    ReplaceGroups.name2id(gff3M)
    gff3M.write(output_gff)
    rm_list = ['WA_sorted.gff', 'other_sorted.gff']
    remove_files_from_list(rm_list)