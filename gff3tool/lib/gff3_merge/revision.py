#!/usr/bin/env python2.7
"""
After the revision of gff file done by annotators (spreadsheet), incorporating the revised information into the Web Apollo gff before gff integration. Additionally, if there are features containing 'replace' field at gene level, add 'replace' field to every child level of the gene and then delete the replace field of the gene.
"""

import sys
import re
import logging
import copy
from gff3tool.lib.gff3 import Gff3


def main(gff_file, revision_file, output_gff, report_file=None, user_defined1=None, auto=True, logger=None):
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    if not logger:
        logger = logger_null

    NCRNA = ['rRNA', 'miRNA', 'ncRNA', 'snRNA', 'snoRNA', 'tRNA']

    logger.info('Reading revision file... ({0:s})'.format(revision_file))
    flines = open(revision_file, 'rb')
    fflag = 0
    revision = {}
    revision_id = {}
    rtype = {}
    for line_raw in flines:
        fflag += 1
        if fflag == 1:
            continue
        else:
            if not re.search('\t\n', line_raw):
                line_strip = line_raw.rstrip('\n')
                tokens = line_strip.split('\t')
                key = '{0:s}:{1:s}-{2:s}:{3:s}:{4:s}'.format(tokens[6], tokens[7], tokens[8], tokens[9], tokens[10])
                revision[key]=[tokens[24], line_strip]
                revision_id[tokens[12]] = [tokens[24], line_strip]
                rtype[tokens[10]] = 1

    logger.info('Reading gff3 file... ({0:s})'.format(gff_file))
    gff3 = Gff3(gff_file=gff_file, logger=logger_null)

    if report_file:
        logger.info('Writing summary report ({0:s})...'.format(report_file))
        report_fh = open(report_file, 'wb')
    else:
        logger.info('Writing summary report: replace_tag_report.txt...')
        report_fh = open('replace_tag_report.txt', 'wb')

    # Validation Summary
    report_fh.write('# GFF3 Revision Report ({0:s})'.format(report_file))
    if gff_file and sys.stdin.isatty():
        report_fh.write(': {0:s} and {1:s}'.format(gff_file, revision_file))
    report_fh.write('\n\n')

    report_fh.write('# Summary\n')

    if len(revision_id) == 0:
        report_fh.write('* Found 0 lines to be revised\n')
    else:
        report_fh.write('* Found {0:d} lines of the revision file\n'.format(len(revision_id)))

    match = 0
    for line in gff3.lines:
        if rtype.has_key(line['type']):
            key = '{0:s}:{1:s}-{2:s}:{3:s}:{4:s}'.format(line['seqid'], str(line['start']), str(line['end']), line['strand'], line['type'])
            if revision_id.has_key(line['attributes']['ID']):
                match += 1
                #if not line['attributes'].has_key('replace'):
                #    line['attributes']['replace'] = revision_id[line['attributes']['ID']][0]
                line['attributes']['replace'] = [revision_id[line['attributes']['ID']][0]]
                revision_id[line['attributes']['ID']][1] = 'hit'
            elif revision.has_key(key):
                tokens = revision[key][1].split('\t')
                if not revision[key][1] == 'hit':
                    report_fh.write('\t- Same genomic region, but different IDs:\t(Annotator){0:s}\t(Gff){1:s}\n'.format(tokens[12], line['attributes']['ID']))
                    match += 1
                    if not line['attributes'].has_key('replace'):
                        line['attributes']['replace'] = [revision[key][0]]
                    revision[key][1] = 'hit'
                else:
                    report_fh.write('\t- Same genomic region, but different IDs and duplicate seuqences at the same location:\t(Location){0:s}\t(Gff){1:s}\n'.format(key, line['attributes']['ID']))
    if match == 0:
        #print '\n[Warning!] No matched lines in the input gff!\n'
        print('\n')
        #sys.exit()
    else:
        report_fh.write('* Found {0:d} matched IDs of the revision file\n'.format(match))
        report_fh.write('* Are there IDs that should be revised, but cannot be found in the gff?\n')
        count = 0
        for v in revision_id.itervalues():
            if not v[1] == 'hit':
                tokens = v[1].split('\t')
                key = '{0:s}:{1:s}-{2:s}:{3:s}:{4:s}'.format(tokens[6], tokens[7], tokens[8], tokens[9], tokens[10])
                if not revision[key][1] == 'hit':
                    report_fh.write('\t- {0:s}\n'.format(v[1]))
                    count += 1
        if count == 0:
            report_fh.write('\t- All IDs are properly found in the gff.\n')

    u_types = set()
    if user_defined1 != None:
        for line in user_defined1:
            u_types.add(line[0])

    roots = []
    transcripts = []
    unique = set()
    for line in gff3.lines:
        if user_defined1 is None:
            try:
                if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                    roots.append(line)
            except KeyError:
                print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
        else:
            if line['type'] in u_types:
                transcripts.append(line)
                for root in gff3.collect_roots(line):
                    if root['line_raw'] not in unique:
                        roots.append(root)
                        unique.add(root['line_raw'])

    #roots = [line for line in gff3.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    for line in roots:
        if line['attributes'].has_key('replace') and line.has_key('children'):
            for index in range(len(line['attributes']['replace'])):
                line['attributes']['replace'][index] = re.sub('\s+', '', line['attributes']['replace'][index])
            if user_defined1 is None:
                children = line['children']
            else:
                children = []
                unique = set()
                if line['type'] in u_types:
                    children.append(line)
                else:
                    for child in gff3.collect_descendants(line):
                        if child['type'] in u_types:
                            if child['line_raw'] not in unique:
                                children.append(child)
                                unique.add(child['line_raw'])
                children = sorted(children, key=lambda k: k['line_index'])
            flag = 0
            for child in children:
                f=0
                if not child['attributes'].has_key('replace'):
                    child['attributes']['replace'] = line['attributes']['replace']
                    flag += 1
                    f+=1

                for index in range(len(child['attributes']['replace'])):
                    child['attributes']['replace'][index] = re.sub('\s+', '', child['attributes']['replace'][index])

                if f == 0:
                    #print('\nReplace tags found at both gene and mRNA level:{0:s}; {1:s}'.format(line['attributes']['replace'], child['attributes']['replace']))
                    i = str(sorted(line['attributes']['replace']))
                    j = str(sorted(child['attributes']['replace']))
                    if not i == j:
                        print '[Warning!] replace tag at gene level ({0:s}) is not consistent with that at mRNA level ({1:s})'.format(i,j)
            if user_defined1 is None:
                del line['attributes']['replace']
            else:
                if line['type'] not in u_types:
                    del line['attributes']['replace']

            # add an exon features with the same coordiantes to the ncRNA feature if the ncRNA does not contain at least one exon.
            if user_defined1 is None:
                children = line['children']
            else:
                children = []
                unique = set()
                if line['type'] in u_types:
                    children.append(line)
                else:
                    for child in gff3.collect_descendants(line):
                        if child['type'] in u_types:
                            if child['line_raw'] not in unique:
                                children.append(child)
                                unique.add(child['line_raw'])
                children = sorted(children, key=lambda k: k['line_index'])
            for child in children:
                exonflag = 0
                if child['type'] in NCRNA:
                    gchildren = child['children']
                    for gchild in gchildren:
                        if gchild['type'] == 'exon':
                            exonflag += 1
                    if exonflag == 0:
                        newid = '{0:s}-EXON1'.format(child['attributes']['ID'])
                        newExon = copy.deepcopy(child)
                        eofindex = len(gff3.lines)
                        newExon['line_index'] = eofindex
                        newExon['parents'] = []
                        newExon['attributes']['Parent']=[]
                        newExon['attributes']['ID'] = newid
                        newExon['attributes']['Name'] = newid
                        newExon['type'] = 'exon'
                        if newExon['attributes'].has_key('replace'):
                           del newExon['attributes']['replace']
                        newExon['parents'].append(child)
                        newExon['attributes']['Parent'].append(child['attributes']['ID'])
                        child['children'].append(newExon)
                        gff3.features[newExon['attributes']['ID']].append(newExon)
                        gff3.lines.append(newExon)

            if line['type'] == 'gene' or line['type'] == 'pseudogene':
                if not line.has_key('children'):
                    gff3.remove(line)
        if auto:
            if line.has_key('children'):
                if user_defined1 is None:
                    children = line['children']
                else:
                    children = []
                    unique = set()
                    if line['type'] in u_types:
                        children.append(line)
                    else:
                        for child in gff3.collect_descendants(line):
                            if child['type'] in u_types:
                                if child['line_raw'] not in unique:
                                    children.append(child)
                                    unique.add(child['line_raw'])
                tags = {}
                for child in children:
                    tag = ','.join(child['attributes']['replace']).replace(' ','')
                    tag = tag.split(',')
                    tags[tuple(tag)] = 0
                # multi-isoforms have different replace tags
                if len(tags) > 1:
                    flag = 0
                    merged_tag = set()
                    for tag in tags.keys():
                        if 'NA' in tag:
                            flag = 1
                        merged_tag.update(list(tag))
                    if flag == 0:
                        for child in children:
                            child['attributes']['replace'] = list(merged_tag)

    if report_file:
        report_fh.close()

    logger.info('Writing revised gff: ({0:s})...'.format(output_gff))
    gff3.write(output_gff)
