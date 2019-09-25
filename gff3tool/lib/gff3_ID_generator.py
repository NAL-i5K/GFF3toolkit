#! /usr/bin/env python
# Contributed by Li-Mei Chiang <dytk2134 [at] gmail [dot] com> (2018)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
import os
import re
import sys
import subprocess
from gff3 import Gff3
import uuid
import string
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

__version__ = '1.0.0'

def TypeSort(line_list, sorting_order, reverse=False):
    id2line ={}
    id2index = {}
    line_list_sort = []
    for line in line_list:
        lineindex = line['start'] if reverse==False else line['end']
        id2line[str(line['line_raw'])] = line
        try:
            if line['type'] in sorting_order:
                id2index[str(line['line_raw'])] = [lineindex, sorting_order[line['type']] if reverse==False else (-sorting_order[line['type']])]
            else:
                id2index[str(line['line_raw'])] = [lineindex, 99 if reverse==False else -99]
        except:
            logger.error('[Start/End] Start/End is not a valid integer. - Line (%s)', str(line['line_index']+1))
    id_sorted = sorted(id2index, key=lambda i: (int(id2index[i][1]), int(id2index[i][0])), reverse=reverse)
    for i in id_sorted:
        line_list_sort.append(id2line[i])
    return line_list_sort
def descendants_list(line_data, level):
    collected_list = []
    if 'children' in line_data:
        children = line_data['children']
        for child in children:
            child['level'] = level
            collected_list.append(child)
            try:
                collected_list.extend(descendants_list(child, level+1))
            except:
                print child['line_errors']
    else:
        return
    return collected_list

def level_list(collected_list):
    leveldict = dict()
    levelList = list()
    for line in collected_list:
        if 'level' in line:
            if line['level'] not in leveldict:
                leveldict[line['level']] = [line]
                levelList.append([])
            else:
                leveldict[line['level']].append(line)
    for key in leveldict:
        levelList[key].extend(leveldict[key])
    return levelList

def idgenerator(prefix, lastnumber, digitlen):
    lastnumber += 1
    idnum = str(lastnumber)
    if len(idnum) < digitlen:
        adddigit = digitlen-len(idnum)
        for i in range(adddigit):
            idnum = str(0) + idnum
    result={}
    result['ID'] = prefix + idnum
    result['maxnum'] = lastnumber
    return(result)
def write_features(line, out_f):
    field_keys = ['seqid', 'source', 'type', 'start', 'end', 'score', 'strand', 'phase']
    field_list = [str(line[k]) for k in field_keys]
    attribute_list = []
    for k, v in line['attributes'].items():
        if isinstance(v, list):
            v = ','.join(v)
        attribute_list.append('%s=%s' % (str(k), str(v)))
    field_list.append(';'.join(attribute_list))
    out_f.write('\t'.join(field_list) + '\n')

def write_gff3(gff3, out_f):
    ignore_directives = ['##sequence-region', '###', '##FASTA']
    wrote_lines = set()
    directives_lines = list()
    wrote_sequence_region = set()
    sequence_regions = {}
    root_lines = []
    with open(out_f, 'w') as out_gff:
        for line in gff3.lines:
            if line['line_type'] == 'feature':
                if 'Parent' not in line['attributes']:
                    root_lines.append(line)
            if line['line_type'] == 'directive' and line['directive'] == '##sequence-region':
                sequence_regions[line['seqid']] = (line['start'], line['end'])
            if line['line_type'] == 'directive' and line['directive'] not in ignore_directives:
                directives_lines.append(line)
        for directives_line in directives_lines:
            out_gff.write(directives_line['line_raw'])
        root_lines = sorted(root_lines, key=lambda k: k['seqid'])
        for root in root_lines:
            lines_wrote = len(wrote_lines)
            if root['line_index'] in wrote_lines:
                continue
            if root['seqid'] not in wrote_sequence_region:
                if root['seqid'] in sequence_regions:
                    out_gff.write('##sequence-region %s %d %d\n' % (root['seqid'], sequence_regions[root['seqid']][0], sequence_regions[root['seqid']][1]))
                wrote_sequence_region.add(root['seqid'])
            write_features(root, out_gff)
            wrote_lines.add(root['line_index'])
            descendants = gff3.descendants(root)
            for descendant in descendants:
                if descendant['line_index'] in wrote_lines:
                    continue
                write_features(descendant, out_gff)
                wrote_lines.add(root['line_index'])
            if lines_wrote != len(wrote_lines):
                out_gff.write('###\n')

def read_merge_report(gff3, merge_report):
    # merge_report file
    # Change_log Original_gene_name Original_transcript_ID Original_transcript_name Tmp_OGSv0_ID
    header_lines = list()
    log_lines = list()
    # merge_report_dict = {'rna84':[0, 2, 5]}
    merge_report_dict = dict()
    header_end = True
    line_num = 0
    with open(merge_report, 'rb') as in_f:
        for line in in_f:
            line = line.strip()
            if line:
                if not line.startswith('#'):
                    if header_end:
                        if 'Change_log' in line:
                            header_end = False
                        header_lines.append(line)
                    else:
                        tokens = line.split('\t')
                        log_lines.append(tokens)
                        if tokens[4] != 'NA':
                            if tokens[4] not in merge_report_dict:
                                merge_report_dict[tokens[4]] = list()
                            merge_report_dict[tokens[4]].append(line_num)
                        line_num += 1
                else:
                    header_lines.append(line)

    return header_lines, log_lines, merge_report_dict

def main(in_gff, merge_report, out_merge_report, out_gff, uuid_on, prefix, digitlen, report, alias):
    logger.info('Reading input gff3 file: (%s)', in_gff)
    gff3 = Gff3(gff_file=in_gff, logger=None)
    if merge_report:
        if not out_merge_report:
            logger.error('-m is given. Please specify the filename of the updated merge report with -om')
            sys.exit(1)
        else:
            logger.info('Reading the update report file generated by gff3_merge program: (%s)', merge_report)
            header_lines, log_lines, merge_report_dict = read_merge_report(gff3, merge_report)
    # generate a table of comparison between old and new IDs.
    if report:
        out_report = open(report, 'w')

    # old and new IDs pair dict
    # ID_dict = {old_ID:newID, missingID: [newID1, newID2]}
    ID_dict = {
        'missing': []
    }
    ID_order = []
    roots = list()
    logger.info('Generate new ID for features in (%s)', in_gff)
    for line in gff3.lines:
        try:
            if line['line_type'] == 'feature':
                if uuid_on:
                    newID = str(uuid.uuid1())
                    if 'ID' in line['attributes']:
                        if line['attributes']['ID'] in ID_dict:
                            ID_dict[line['attributes']['ID']].append(newID)
                            if alias:
                                line['attributes']['Alias'] = line['attributes']['ID']
                            line['attributes']['ID'] = newID
                        else:
                            ID_dict[line['attributes']['ID']] = [newID]
                            ID_order.append(line['attributes']['ID'])
                            if alias:
                                line['attributes']['Alias'] = line['attributes']['ID']
                            line['attributes']['ID'] = newID
                    else:
                        ID_dict['missing'].append(newID)
                        line['attributes']['ID'] = newID
                    if 'Parent' in line['attributes']:
                        for index, parent in enumerate(line['attributes']['Parent']):
                            if parent in ID_dict:
                                line['attributes']['Parent'][index] = ID_dict[parent][0]
                            else:
                                newID = str(uuid.uuid1())
                                ID_dict[parent] = [newID]
                                ID_order.append(parent)
                                line['attributes']['Parent'][index] = newID
                else:
                    if 'Parent' not in line['attributes']:
                        roots.append(line)
        except KeyError:
            logger.warning('[Missing Attributes] Line (%s)', str(line['line_index'] + 1))
    IDnumber = 0
    for root in roots:
        newID = idgenerator(prefix, IDnumber, digitlen)
        IDnumber = newID['maxnum']
        ID_dict[root['attributes']['ID']] = [newID['ID']]
        ID_order.append(root['attributes']['ID'])
        if alias: 
            root['attributes']['Alias'] = root['attributes']['ID']
        root['attributes']['ID'] = newID['ID']
        children = root['children']
        alphabets = list(string.ascii_uppercase)
        for child in children:
            for index, parent in enumerate(child['attributes']['Parent']):
                if parent in ID_dict:
                    child['attributes']['Parent'][index] = newID['ID']

            newcID = '%s-R%s' % (newID['ID'], alphabets.pop(0))
            ID_dict[child['attributes']['ID']] = [newcID]
            ID_order.append(child['attributes']['ID'])
            if alias:
                child['attributes']['Alias'] = child['attributes']['ID']
            child['attributes']['ID'] = newcID
            collected_list = descendants_list(line_data=child, level=0)
            levellist = level_list(collected_list)
            IDnumber_dict = dict()
            for item_list in levellist:
                reverse = False
                if len(item_list) > 1:
                    if item_list[0]['strand'] == '-':
                        reverse = True
                descendant_sort = TypeSort(item_list, dict(), reverse)
                for descend in descendant_sort:
                    flag = False
                    if descend['type'] not in IDnumber_dict:
                        IDnumber_dict[descend['type']] = 0
                    for index, parent in enumerate(descend['attributes']['Parent']):
                        if parent in ID_dict:
                            if flag == True:
                                break
                            if descend['attributes']['ID'] not in ID_dict:
                                deprefix = '%s-%s' % (ID_dict[parent][0], descend['type'])
                                newdID = idgenerator(deprefix, IDnumber_dict[descend['type']], 3)
                                IDnumber_dict[descend['type']] = newdID['maxnum']
                                ID_dict[descend['attributes']['ID']] = [newdID['ID']]
                                ID_order.append(descend['attributes']['ID'])
                                descend['attributes']['ID'] = newdID['ID']
                                flag = True
                            if flag == False:
                                deprefix = '%s-%s' % (ID_dict[parent][0], descend['type'])
                                newdID = idgenerator(deprefix, IDnumber_dict[descend['type']], 3)
                                IDnumber_dict[descend['type']] = newdID['maxnum']
                                ID_dict[descend['attributes']['ID']].append(newdID['ID'])
                                descend['attributes']['ID'] = newdID['ID']
                                flag = True
                            descend['attributes']['Parent'][index] = ID_dict[parent][0]
    if merge_report and out_merge_report:
        logger.info('Update report file generated by gff3_merge program with new IDs.')
        with open(out_merge_report, 'w') as out_f:
            for header_line in header_lines:
                out_f.write(header_line + '\n')
            for key in merge_report_dict:
                if key not in ID_order:
                    logger.error('The report file has to correspond to the gff3 file specified with -g')
                    sys.exit(1)
                else:
                    for line_num in merge_report_dict[key]:
                        # update Tmp_OGSv0_ID
                        log_lines[line_num][4] = ID_dict[key][0]
            for log_line in log_lines:
                out_f.write('\t'.join(log_line) + '\n')
    logger.info('Write out gff3 file: (%s)', out_gff)
    write_gff3(gff3, out_gff)
    if report:
        ID_order.append('missing')
        logger.info('Generate a report of comparison between old and new IDs: (%s)', report)
        out_line = 'Old_ID\tNewID'
        out_report.write(out_line+'\n')
        for key in ID_order:
            for value in ID_dict[key]:
                out_line = '%s\t%s' % (key, value)
                out_report.write(out_line+'\n')

        out_report.close()

if __name__ == '__main__':
    import argparse
    from textwrap import dedent
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=dedent("""\

    Quick start:
    python %(prog)s -g in.gff3 -og out.gff -uuid -r report.txt
    """))
    parser.add_argument('-g', '--gff', type=str, help='GFF3 file', required=True)
    parser.add_argument('-og', '--output_gff', type=str, help='Output GFF3 file', required=True)
    parser.add_argument('-m', '--merge_report', type=str, help='Update report file generated by gff3_merge program with new IDs. The report file has to correspond to the gff3 file specified with -g')
    parser.add_argument('-om', '--out_merge_report', type=str, help='Filename of the updated merge report.')
    parser.add_argument('-uuid', '--universally_unique_identifier', action="store_true", help='Use Universally Unique Identifier as the new ID for features in GFF3 file. (Default: False)', default=False)
    parser.add_argument('-idpre', '--idprefix', type=str, help='ID prefix (Default: MODEL).', default='MODEL')
    parser.add_argument('-diglen', '--digitlen', type=int, help='Length of digit.', default=6)
    parser.add_argument('-r', '--report', type=str, help='Generate a table of comparison between old and new IDs.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-a', '--alias', action='store_true', default=False, help='Specify this argument if you want old IDs to be retained in the gff3 file as an Alias attribute')

    args = parser.parse_args()
    main(in_gff=args.gff, merge_report=args.merge_report, out_merge_report=args.out_merge_report, out_gff=args.output_gff, uuid_on=args.universally_unique_identifier, prefix=args.idprefix, digitlen=args.digitlen, report=args.report, alias=args.alias)
