#! /user/local/bin/python2.7
# -*- coding: utf-8 -*-

from collections import defaultdict
import re
import copy
import logging
logger = logging.getLogger(__name__)

def fasta_dict_to_file(fasta_dict, fasta_file, line_char_limit=None):
    """Write fasta_dict to fasta_file
    :param fasta_dict: returned by fasta_file_to_dict
    :param fasta_file: output file can be a string path or a file object
    :param line_char_limit: None = no limit (default)
    :return: None
    """
    fasta_fp = fasta_file
    if isinstance(fasta_file, str):
        fasta_fp = open(fasta_file, 'wb')

    for key in fasta_dict:
        seq = fasta_dict[key]['seq']
        if line_char_limit:
            seq = '\n'.join([seq[i:i+line_char_limit] for i in range(0, len(seq), line_char_limit)])
        fasta_fp.write(u'{0:s}\n{1:s}\n'.format(fasta_dict[key]['header'], seq))

def remove_duplicate_trans(gff3, error_list, logger):
    """
    Emr0001 : Duplicate transcript found
    """
    #remove specified transcript
    for error in error_list:
        remove_lines = error[1:]
        for remove_line in remove_lines:
            gff3.lines[remove_line-1]['line_status'] = 'removed'
            for child in gff3.collect_descendants(gff3.lines[remove_line-1]):
                child['line_status'] = 'removed'
            # check if there is any child feature remained in the  gene model. If not, reomve this gene model
            for root in gff3.collect_roots(gff3.lines[remove_line-1]):
                flag = True
                for child in gff3.collect_descendants(root):
                    if child['line_status'] != 'removed':
                        flag = False
                if flag == True:
                    root['line_status'] = 'removed'


def delete_model(gff3, error_list, logger):
    """
    Delete models:
    Esf0003 : strand information missing
    Esf0002 : Start/End is not a valid 1-based integer coordinate
    Esf0017 : Start/End is not a valid integer
    Esf0018 : Start is not less than or equal to end
    Esf0022 : Features should contain 9 fields
    Esf0025 : Strand has illegal characters
    Ema0007 : CDS and parent feature on different strands
    """
    # delete the whole model
    for error in error_list:
        for remove_line in error:
            for root in gff3.collect_roots(gff3.lines[remove_line-1]):
                root['line_status'] = 'removed'
                for child in gff3.collect_descendants(root):
                    child['line_status'] = 'removed'


def fix_boundary(gff3, error_list=None, line=None, logger=logger):
    """
    Ema0001 : Parent feature start and end coordinates exceed those of child features
    Ema0003 : This feature is not contained within he parent feature coordinates
    """

    # Check if the 'line_status' is 'removed'. If so, ignore that line.
    # assume the first-level is gene feature and the second-level is transcript feature
    if line != None:
        for root in gff3.collect_roots(line):
            cPos = []
            for child in root['children']:
                gcPos = []
                for grandchild in child['children']:
                    gcPos.append(grandchild['start'])
                    gcPos.append(grandchild['end'])
                maxgc = max(gcPos)
                mingc = min(gcPos)
                child['start'] = mingc
                child['end'] = maxgc
                cPos.append(child['start'])
                cPos.append(child['end'])
            maxc = max(cPos)
            minc = min(cPos)
            root['start'] = minc
            root['end'] = maxc
    else:
        for error in error_list:
            for line_num in error:
                if gff3.lines[line_num-1]['line_status'] != 'removed':
                    for root in gff3.collect_roots(gff3.lines[line_num-1]):
                        cPos = []
                        for child in root['children']:
                            gcPos = []
                            for grandchild in child['children']:
                                gcPos.append(grandchild['start'])
                                gcPos.append(grandchild['end'])
                            maxgc = max(gcPos)
                            mingc = min(gcPos)
                            child['start'] = mingc
                            child['end'] = maxgc
                            cPos.append(child['start'])
                            cPos.append(child['end'])
                        maxc = max(cPos)
                        minc = min(cPos)
                        root['start'] = minc
                        root['end'] = maxc



def pseudogene(gff3, error_list, logger):
    """
    Ema0005 : Pseudogene has invalid child feature type
    Esf0001 : Feature type may need to be changed to pseudogene
    """
    # first-level -> pseudogene; second-level -> pseudogenic_transcript; third-level(exon) -> pseudogenic_exon
    # change mRNA to pseudogenic_transcript; change exon to pseudogenic_exon; remove CDS lines mRNA in the type of pseudogene found pseudogene or not?
    for error in error_list:
        for line_num in error:
            if gff3.lines[line_num-1]['line_status'] != 'removed':
                for root in gff3.collect_roots(gff3.lines[line_num-1]):
                    root['type'] = 'pseudogene'
                    for child in root['children']:
                        child['type'] = 'pseudogenic_transcript'
                        for grandchild in child['children']:
                            if grandchild['type'] == 'CDS':
                                grandchild['line_status'] = 'removed'
                                # remove child feature of CDS
                                for CDS_child in gff3.collect_descendants(grandchild):
                                    CDS_child['line_status'] = 'removed'
                            elif grandchild['type'] == 'exon':
                                grandchild['type'] = 'pseudogenic_exon'



def split(gff3, error_list, logger):
    """
    Ema0009 : Incorrectly merged gene parent? Isoforms that do not share coding sequences are found
    """
    for error in error_list:
        for line_num in error:
            if gff3.lines[line_num-1]['line_status'] != 'removed':
                eofindex = len(gff3.lines) - 1
                for root in gff3.collect_roots(gff3.lines[line_num-1]):
                    oldID = 'NA'
                    try:
                        oldID = root['attributes']['ID']
                        old_feature = gff3.features[oldID]
                        if root['attributes'].has_key('modified_track') and root['attributes']['modified_track'] == 'removed':
                            continue
                    except KeyError:
                        logger.warning('[Missing ID] - Line %s', str(line_num))
                    children = root['children']
                    hitpair = []
                    childrenlist = []
                    for i in range((len(children)-1)):
                        c1 = children[i]
                        childrenlist.append(c1['attributes']['ID'])
                        for j in range((i+1), (len(children))):
                            c2 = children[j]
                            hit = 0
                            if gff3.overlap(c1, c2):
                                gchildren1 = c1['children']
                                gchildren2 = c2['children']
                                for gc1 in gchildren1:
                                    for gc2 in gchildren2:
                                        if gff3.overlap(gc1, gc2):
                                            hit += 1
                            if hit > 0:
                                pair = ' '.join([c1['attributes']['ID'], c2['attributes']['ID']])
                                hitpair.append(pair)
                    childrenlist.append(children[len(children)-1]['attributes']['ID'])
                    childgroup = connected_compoents(childrenlist, hitpair)
                    flag = 1
                    for i, val in enumerate(childgroup):
                        newID = ''
                        if root['attributes'].has_key('modified_track'):
                            newID = '{0:s}.s{1:d}'.format(root['attributes']['modified_track'], flag)
                        else:
                            newID = '{0:s}.s{1:d}'.format(oldID, flag)
                        newparent = copy.deepcopy(root)
                        newparent['attributes']['ID'] = newID
                        if newparent['attributes'].has_key('Name') and newparent['attributes']['Name'] == newparent['attributes']['ID']:
                            newparent['attributes']['Name'] = newID
                        eofindex += 1
                        newparent['line_index'] = eofindex
                        newparent['children'] = []
                        for j in val:
                            children = gff3.features[j]
                            for child in children:
                                newparent['children'].append(child)
                        if newparent['attributes'].has_key('modified_track'):
                            del newparent['attributes']['modified_track']
                        gff3.features[newID].append(newparent)
                        gff3.lines.append(newparent)
                        # update the child's parent list and parent attribute
                        for j in val:
                            children = gff3.features[j]
                            for child in children:
                                child['parents'] = []
                                child['parents'].append(gff3.features[newID])
                                child['attributes']['Parent']=[]
                                child['attributes']['Parent'].append(newID)
                                child['line_status'] = 'split'
                                # make gene boundary to go with mRNA boundary
                                fix_boundary(gff3 = gff3, line = child, logger = logger)
                        flag += 1
                    # remove the old model's children list and then remove the old model
                    for old_ld in old_feature:
                        old_ld['children'] = []
                    root['line_status'] = 'removed'

def connected_compoents(child_list, pair_list):
    # The graph nodes
    class Data(object):
        def __init__(self, name):
            self.__name  = name
            self.__links = set()
        @property
        def name(self):
            return self.__name
        @property
        def links(self):
            return set(self.__links)
        def add_link(self, other):
            self.__links.add(other)
            other.__links.add(self)
    # The function to look for connected components.
    def cc(nodes):
        # List of connected components found. The order is random.
        result = []
        # Make a copy of the set, so we can modify it.
        nodes = set(nodes)
        # Iterate whild we still have nodes to process.
        while nodes:
            # Get a random node and remove it from the global set.
            n = nodes.pop()
            # This set will contain the next group of nodes connected to each other.
            group = {n}
            # Build a queue with this node in it.
            queue = [n]
            # Iterate the queue.
            # When it's empty, we finished visiting a group of connected nodes.
            while queue:
                # Consume the next item from the queue.
                n = queue.pop(0)
                # Fetch the neighbors.
                neighbors = n.links
                # Remove the neighbors we already visited.
                neighbors.difference_update(group)
                # Remove the remaining nodes from the global set.
                nodes.difference_update(neighbors)
                    # Add them to the group of connected nodes.
                group.update(neighbors)
                    # Add them to the queue, so we visit them in the next iterations.
                queue.extend(neighbors)
                # Add the group to the list of groups.
            result.append(group)
        # Return the list of groups.
        return result
    nodelist = {}
    for child in child_list:
        nodelist[child] = Data(child)
    for pair in pair_list:
        tokens = pair.split(' ')
        nodelist[tokens[0]].add_link(nodelist[tokens[1]])
    nodes=set()
    for v in nodelist.itervalues():
        nodes.add(v)
    result=[]
    for components in cc(nodes):
        names = sorted(node.name for node in components)
        result.append(names)
    return result


def merge(gff3, error_list, logger):
    """
    Emr0002 : Incorrectly split gene parent?
    """
    # join overlap error list
    error_list_dict = {}
    updated_error_list = []
    for error in error_list:
        if len(error) == 2:
            if error[0] not in error_list_dict:
                error_list_dict[error[0]] = set([error[0],error[1]])
            if error[1] not in error_list_dict:
                error_list_dict[error[1]] = set([error[0],error[1]])
            for element in set(error_list_dict[error[0]]):
                error_list_dict[element].update(error_list_dict[error[1]])
            for element in set(error_list_dict[error[1]]):
                error_list_dict[element].update(error_list_dict[error[0]])
        else:
            logger.warning('The length of error line list is not equal to 2.')
    for error in error_list_dict.values():
        error = list(error)
        error.sort()
        if error not in updated_error_list:
            updated_error_list.append(error)

    # assume the 'parent' feature of a transcript is a 'root' feature
    # Merge wrongly split model
    for error in updated_error_list:
        Merge_trans = []
        Old_ID_list = []
        eofindex = len(gff3.lines)-1
        for line_num in error:
            if gff3.lines[line_num-1]['line_status'] != 'removed':
                Merge_trans.append(gff3.lines[line_num-1])
                for root in gff3.collect_roots(gff3.lines[line_num-1]):
                    try:
                        Old_ID_list.append(root['attributes']['ID'])
                    except:
                        logger.warning('[Missing ID] - Line %s', str(root['line_index']+1))

        if len(Merge_trans) > 1:
            parents = Merge_trans[0]['parents']
            flag = 1
            for parent in parents:
                for p in parent:
                    oldID = p['attributes']['ID']
                    newID = '{0:s}.m{1:d}'.format(oldID, flag)
                    if newID in gff3.features:
                        import uuid
                        newID = str(uuid.uuid1())
                    newparent = copy.deepcopy(p)
                    newparent['attributes']['ID'] = newID
                    if newparent['attributes'].has_key('Name'):
                        if newparent['attributes']['Name'] == newparent['attributes']['ID']:
                            newparent['attributes']['Name'] = newID
                    eofindex += 1
                    newparent['line_index'] = eofindex
                    # update the child's parent list and parent attribute
                    newparent['children'] = []
                    children_id = []

                    for children in Merge_trans:
                        try:
                            children_id.append(children['attributes']['ID'])
                            child_features = gff3.features[children['attributes']['ID']]
                            for child in child_features:
                                newparent['children'].append(child)
                        except:
                            logger.warning('[Missing ID] - Line %s', str(children['line_index']+1))

                    gff3.features[newID].append(newparent)
                    gff3.lines.append(newparent)

                    for child_id in children_id:
                        children = gff3.features[child_id]
                        for child in children:
                            child['parents'] = [gff3.features[newID]]
                            child['attributes']['Parent'] = [newID]
                            child['line_status'] = 'merge'
                            # make gene boundary to go with transcript boundary
                            fix_boundary(gff3=gff3, line=child, logger=logger)

                    flag += 1
                    # update new model line_index


            # remove the old model
            for ID in Old_ID_list:
                for root in gff3.features[ID]:
                    children = root['children']
                    child_num = 0
                    for child in children:
                        try:
                            if child['attribute']['ID'] not in children_id:
                                child_num += 1
                            else:
                                gff3.lines[child['line_index']]['line_status'] = 'removed'
                                for grandchild in gff3.collect_descendants(child):
                                    gff3.lines[grandchild['line_index']]['line_status'] = 'removed'
                        except:
                            logger.warning('[Missing ID] - Line %s', str(child['line_index']+1))

                    if child_num == 0:
                        gff3.lines[root['line_index']]['line_status'] = 'removed'
                        gff3.lines[root['line_index']]['children'] = []



def fix_phase(gff3, error_list, line_num_dict, logger):
    """
    Ema0006 : Wrong phase
    Esf0026 : Phase is not 0, 1, or 2, or not a valid integer
    Esf0027 : Phase is required for all CDS features
    """
    #valid_CDS_phase = set([0,1,2])
    valid_phase = set((0, 1, 2))
    for error in error_list:
        for line_num in error:
            if gff3.lines[line_num-1]['line_status'] != 'removed':
                for root in gff3.collect_roots(gff3.lines[line_num-1]):
                    CDS_list = []
                    CDS_set = set()
                    if root['type'] != 'CDS':
                        root['phase'] = '.'
                    for child in gff3.collect_descendants(root):
                        if child['type'] == 'CDS':
                            if child['line_raw'] not in CDS_set:
                                CDS_list.append(child)
                                CDS_set.add(child['line_raw'])
                        else:
                            gff3.lines[child['line_index']]['phase'] = '.'
                    if len(CDS_list) != 0:
                        if CDS_list[0]['strand'] == '-':
                            sorted_CDS_list = sorted(CDS_list, key=lambda x: x['end'], reverse=True)
                        elif CDS_list[0]['strand'] == '+':
                            sorted_CDS_list = sorted(CDS_list, key=lambda x: x['start'])
                    if sorted_CDS_list[0]['line_index']+1 in error:
                        if 'Ema0006' in line_num_dict[sorted_CDS_list[0]['line_index']+1]:
                            phase = map(int,re.findall(r'\d',line_num_dict[sorted_CDS_list[0]['line_index']+1]['Ema0006']))[1]
                        else:
                            try:
                                phase = sorted_CDS_list[0]['phase']
                                if phase not in valid_phase:
                                    phase = 0
                            except ValueError:
                                phase = 0
                        gff3.lines[sorted_CDS_list[0]['line_index']]['phase'] = phase

                    else:
                        phase = sorted_CDS_list[0]['phase']
                    for CDS in sorted_CDS_list:
                        if CDS['phase'] != phase:
                            gff3.lines[CDS['line_index']]['phase'] = phase
                        phase = (3 - ((CDS['end'] - CDS['start'] + 1 - phase) % 3)) % 3




def remove_directive(gff3, error_list, logger):
    """
    Esf0016: ##sequence-region seqid may only appear once
    Esf0020: Version is not a valid integer
    Esf0021: Unknown directive
    """
    for error in error_list:
        for line_num in error:
            gff3.lines[line_num-1]['line_type'] = 'unknown'


def add_gff3_version(gff3, logger):
    """
    Esf0014 : ##gff-version missing from the first line
    """
    #
    line_data = {
                'line_index': 0,
                'line_raw': '##gff-version 3\n',
                'line_status': 'normal',
                'parents': [],
                'children': [],
                'line_type': 'directive',
                'directive': '##gff-version',
                'line_errors': [],
                'type': '',
                'version': 3
            }
    for line in gff3.lines:
        line['line_index'] += 1
    gff3.lines.insert(0, line_data)



def fix_attributes(gff3, error_list, logger):
    '''
    Esf0030 : Empty attribute tag
    Esf0031 : Empty attribute value
    Esf0029 : Attribute must contain one and only one equal (=) sign
    Esf0034 : Attribute has identical values (count, value)
    Esf0041 : Unknown reserved (uppercase) attribute
    Esf0032 : Found multiple attirbute tags
    Esf0036 : Value of a attribute contains unescaped ","
    Esf0033 : Found ", " in a attribute, possible unescaped
    '''

    unescaped_field = re.compile(r'[\x00-\x1f\x7f]|%(?![0-9a-fA-F]{2})').search
    multi_value_attributes = set(['replace', 'Parent', 'Alias', 'Note', 'Dbxref', 'Ontology_term'])
    reserved_attributes = set(['replace','ID', 'Name', 'Alias', 'Parent', 'Target', 'Gap', 'Derives_from', 'Note', 'Dbxref', 'Ontology_term', 'Is_circular'])
    for error in error_list:
        for line_num in error:
            if gff3.lines[line_num-1]['line_status'] != 'removed':
                tokens = map(str.strip, gff3.lines[line_num-1]['line_raw'].split('\t'))
                if unescaped_field(tokens[8]):
                    # don't know how to fix this
                    pass
                attribute_tokens = tuple(tuple(t for t in a.split('=')) for a in tokens[8].split(';') if a)
                fixed_attributes = {}
                if len(attribute_tokens) == 1 and len(attribute_tokens[0]) == 1 and attribute_tokens[0][0] == '.':
                    pass # no attributes
                else:
                    for a in attribute_tokens:
                        if len(a) != 2:
                            # Esf0029
                            attribute = "=".join(a)
                            equal_pos = [i for i, ltr in enumerate(attribute) if ltr == '=']
                            for equal in equal_pos[1:]:
                                attribute = attribute[:equal] + attribute[equal+1:]
                            a = attribute.split('=')
                        try:
                            tag, value = a
                        except ValueError:
                            tag, value = a[0], ''
                        if not tag:
                            # Esf0030
                            continue
                        if not value.strip():
                            # Esf0031
                            continue
                        if tag in fixed_attributes:
                            # Esf0032
                            if tag not in multi_value_attributes:
                                values = fixed_attributes[tag].split("%2C")
                                if value in values:
                                    continue
                                else:
                                    fixed_attributes[tag] = fixed_attributes[tag] + '%2C' + value

                        if tag in multi_value_attributes:
                            if value.find(', ') >= 0 or value.find(' ,') >= 0:
                                value = value.replace(', ', '%2C')
                                value = value.replace(' ,', '%2C')
                            if tag in fixed_attributes:
                                if tag == 'Note': # don't check for duplicate notes
                                    continue
                                else:
                                    fixed_attributes[tag].extend([s for s in value.split(',') if s not in fixed_attributes[tag]])
                            else:
                                fixed_attributes[tag] = value.split(',')
                            # check for duplicate values
                            if tag != 'Note' and len(fixed_attributes[tag]) != len(set(fixed_attributes[tag])):
                                # remove duplicate
                                fixed_attributes[tag] = list(set(fixed_attributes[tag]))
                        elif tag == 'Target':
                            if value.find(',') >= 0:
                                value = value.replace(',','%2C')
                            target_tokens = value.split(' ')
                            fixed_attributes[tag] = {}
                            try:
                                fixed_attributes[tag]['target_id'] = target_tokens[0]
                                try:
                                    fixed_attributes[tag]['start'] = int(target_tokens[1])
                                except ValueError:
                                    fixed_attributes[tag]['start'] = target_tokens[1]
                                try:
                                    fixed_attributes[tag]['end'] = int(target_tokens[2])
                                except ValueError:
                                    fixed_attributes[tag]['end'] = target_tokens[2]
                                fixed_attributes[tag]['strand'] = target_tokens[3]
                            except IndexError:
                                pass
                        elif tag not in fixed_attributes:
                            if value.find(',') >= 0:
                                value = value.replace(',','%2C')
                            if tag[:1].isupper() and tag not in reserved_attributes:
                                tag = tag[0].lower() + tag[1:]
                            fixed_attributes[tag] = value
                gff3.lines[line_num-1]['attributes'] = fixed_attributes

def write(gff3, output_gff, embed_fasta=None, fasta_char_limit=None, logger=None):
    gff_fp = output_gff
    if isinstance(output_gff, str):
        gff_fp = open(output_gff, 'wb')

    wrote_sequence_region = set()
    # build sequence region data
    sequence_regions = {}
    if gff3.fasta_external:
        for seqid in gff3.fasta_external:
            sequence_regions[seqid] = (1, len(gff3.fasta_external[seqid]['seq']))
    elif gff3.fasta_embedded:
        for seqid in gff3.fasta_embedded:
            sequence_regions[seqid] = (1, len(gff3.fasta_embedded[seqid]['seq']))
    else:
        directives_lines = [line_data for line_data in gff3.lines if line_data['line_type'] == 'directive' and line_data['directive'] == '##sequence-region']
        for sequence_region in directives_lines:
            sequence_regions[sequence_region['seqid']] = (sequence_region['start'], sequence_region['end'])


    wrote_lines = set()
    field_keys = ['seqid', 'source', 'type', 'start', 'end', 'score', 'strand', 'phase']
    reserved_attributes = ['ID', 'Name', 'Alias', 'Parent', 'Target', 'Gap', 'Derives_from', 'Note', 'Dbxref', 'Ontology_term', 'Is_circular']
    attributes_sort_map = defaultdict(int, zip(reserved_attributes, range(len(reserved_attributes), 0, -1)))
    def write_feature(line_data):
        if line_data['line_status'] == 'removed':
            return
        field_list = [str(line_data[k]) for k in field_keys]
        attribute_list = []
        try:
            for k, v in sorted(line_data['attributes'].items(), key=lambda x: attributes_sort_map[x[0]], reverse=True):
                if isinstance(v, list):
                    v = ','.join(v)
                attribute_list.append('%s=%s' % (str(k), str(v)))
            field_list.append(';'.join(attribute_list))
            gff_fp.write('\t'.join(field_list) + '\n')
            wrote_lines.add(line_data['line_index'])
        except:
            logger.warning('[Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line_data['line_index']+1), line_data['line_raw']))
    # write directives
    ignore_directives = ['##sequence-region', '###', '##FASTA']
    directives_lines = [line_data for line_data in gff3.lines if line_data['line_type'] == 'directive' and line_data['directive'] not in ignore_directives]
    for directives_line in directives_lines:
        gff_fp.write(directives_line['line_raw'])

    # write features
    # get a list of root nodes
    root_lines = [line_data for line_data in gff3.lines if line_data['line_type'] == 'feature' and not line_data['parents']]
    root_lines = sorted(root_lines, key=lambda k: k['seqid'])
    for root_line in root_lines:
        lines_wrote = len(wrote_lines)
        if root_line['line_index'] in wrote_lines:
            continue
        # write #sequence-region if new seqid
        if root_line['seqid'] not in wrote_sequence_region:
            if root_line['seqid'] in sequence_regions:
                gff_fp.write('##sequence-region %s %d %d\n' % (root_line['seqid'], sequence_regions[root_line['seqid']][0], sequence_regions[root_line['seqid']][1]))
            wrote_sequence_region.add(root_line['seqid'])
        try:
            root_feature = gff3.features[root_line['attributes']['ID']]
        except KeyError:
            root_feature = [root_line]
        for line_data in root_feature:
            write_feature(line_data)
        descendants = gff3.descendants(root_line)
        for descendant in descendants:
            if descendant['line_index'] in wrote_lines:
                continue
            write_feature(descendant)
        # check if we actually wrote something
        if lines_wrote != len(wrote_lines):
            gff_fp.write('###\n')
    # write fasta
    fasta = embed_fasta or gff3.fasta_external or gff3.fasta_embedded
    if fasta and embed_fasta != False:
        gff_fp.write('##FASTA\n')
        fasta_dict_to_file(fasta, gff_fp, line_char_limit=fasta_char_limit)

    if isinstance(output_gff, str):
        gff_fp.close()




def main(gff3, output_gff, error_dict, line_num_dict, logger=None):
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    fix_ordering = ['Esf0022','Esf0003','Esf0025','Esf0017','Esf0002','Esf0018','Ema0007','Emr0001','Esf0020','Esf0016','Esf0021','Esf0013','Esf0001','Ema0005','Ema0001','Ema0003','Ema0006','Esf0027','Esf0026','Esf0030','Esf0031','Esf0029','Esf0034','Esf0041','Esf0032','Esf0028','Esf0036','Esf0033','Ema0009','Emr0002','Esf0014']
    for error_code in fix_ordering:
        if error_code in error_dict:
            # delete_model
            if error_code in ['Esf0022','Esf0003','Esf0025','Esf0017','Esf0002','Esf0018','Ema0007']:
                #print('delet_model\n')
                delete_model(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Emr0001':
                #print('reomve_duplicate_trans\n')
                remove_duplicate_trans(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Esf0020', 'Esf0016', 'Esf0021']:
                #print('remove_directive\n')
                remove_directive(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Esf0001','Ema0005']:
                #print('pseudogene\n')
                pseudogene(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Ema0001', 'Ema0003']:
                #print('fix_boundary\n')
                fix_boundary(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Ema0006','Esf0027','Esf0026']:
                #print('fix_phase\n')
                fix_phase(gff3=gff3, error_list=error_dict[error_code], line_num_dict=line_num_dict, logger=logger)
            elif error_code in ['Esf0030','Esf0031','Esf0029','Esf0034','Esf0041','Esf0032','Esf0028','Esf0036','Esf0033']:
                #print('fix_attributes\n')
                fix_attributes(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Ema0009':
                #print('split\n')
                split(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Emr0002':
                #print('merge\n')
                merge(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Esf0014':
                #print('add_gff3_version\n')
                add_gff3_version(gff3=gff3, logger=logger)

    write(gff3=gff3,output_gff=output_gff,logger=logger)





