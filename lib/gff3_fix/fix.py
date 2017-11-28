#! /user/local/bin/python2.7
# -*- coding: utf-8 -*-

from collections import defaultdict
from itertools import groupby
import sys
import re
import copy
import logging
from gff3_modify import gff3
logger = logging.getLogger(__name__)


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

def replace_percent_control_sign(gff3, error_list, logger):
    """
    Esf0028 : Attributes must escape the percent (%) sign and any control characters
    """
    # unescaped_field = re.compile(r'[\x00-\x1f\x7f]|%(?![0-9a-fA-F]{2})').search
    # if unescaped_field(tokens[8]):
    for error in error_list:
        for remove_line in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                try:
                    attribute_dict = gff3.lines[remove_line-1]['attributes'].copy()
                    for tag, value in attribute_dict.items():
                        if unescaped_field()
                            
                            gff3.lines[remove_line -1]['attributes'][tag] = value                            
                except:
                    logger.warning('[Missing Attribute] - Line (%s)', str(remove_line))

def fix_boundary(gff3=gff3, error_list=None, line=None, logger=logger):
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
                if gff3.lines[remove_line-1]['line_status'] != 'removed':
                    for root in gff3.collect_roots(gff3.lines[remove_line-1]):
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
                        maxc = man(cPos)
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
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                for root in gff3.collect_roots(gff3.lines[remove_line-1]):
                    root['type'] = 'pseudogene'
                    for child in root['children']:
                        child['type'] = 'pseudogenic_transcript'
                        for grandchild in child['children']:
                            if granschild['type'] == 'CDS':
                                granschild['line_status'] = 'removed'
                            elif granschild['type'] == 'exon':
                                grandchild['type'] = 'pseudogenic_exon'
            


def split(gff3, error_list, logger):
    """
    Ema0009 : Incorrectly merged gene parent? Isoforms that do not share coding sequences are found
    """
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                for root in gff3.collect_roots(gff3.lines[remove_line-1]):
                    oldID = 'NA'
                    try:
                        oldID = root['attribute']['ID']
                        old_feature = gff3.features[oldID]
                        if root['attributes'].has_key('modified_track') and root['attributes']['modified_track'] == 'removed':
                            continue
                    except:
                        logger.warning('[Missing ID] - Line %s', str(remove_line))
                    children = root['children']
                    gflag = 1
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
                    for i in range(len(childgroup)):
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
                    for j in childgroup[i]:
                        children = gff3.features[j]
                        for child in children:
                            newparent['children'].append(child)
                    newparent['attributes']['modified_track'] = newID
                    gff3.features[newID].append(newparent)
                    gff3.lines.append(newparent)
                    # update the child's parent list and parent attribute 
                    for j in childgroup[i]:
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
                root['attributes']['modified_track'] = 'removed'
def connected_compoents(self, child_list, pair_list):
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
        for k,v in nodelist.items():
            nodes.add(v)
        result=[]
        for components in cc(nodes):
            names = sorted(node.name for node in components)
            result.append(names)
        return result


def merge():
    """
    Emr0002 : Incorrectly split gene parent?
    """
    # Merge wrongly split model
    def construct_vector(line):
        name_filed = ['Name']
        fields = ['symbol', 'status', 'description', 'Note', 'Dbxref']
        vector = []
        nameflag = 0
        if line['attributes'].has_key(name_field[0]):
            nameflag += 1
            line['attributes'][name_field[0]] = re.sub('\s+$', '', line['attributes'][name_field[0]])
            if line['attributes']['ID'] == line['attributes'][name_field[0]]:
                vector.append({0:'NA'})
            else:
                vector.append({1:line['attributes']['Name']})
        if nameflag == 0:
            vector.append({0:'NA'})
        for f in fields:
            if line['attributes'].has_key(f):
                line['attributes'][f] = re.sub('\s+$', '', str(line['attributes'][f]))
                vector.append({1:line['attributes'][f]})
            else:
                vector.append({0:'NA'})
        return vector
    def compare_vectors(list1, list2):
        result=[]
        for i in range(len(list1)):
            for k1,v1 in list1[i].items():
                for k2,v2 in list2[i].items():
                    c=0
                    if k1==1 and k2==1:
                        if v1 == v2:
                            c=1
                    result.append([k1,k2,c])
        return result
    def compress_matrix(matrix):
        # All keys must be string!!!
        map_compressed_code={'0':3, '1':1, '2':0, '3':3}
        unique={}
        str2list={}
        for i in matrix:
            compressed_code = sum(i)
            unique[str(i)] = map_compressed_code[str(compressed_code)]
            str2list[str(i)] = i

        code1sum={}
        for k,v in unique.items():
            if v == 1:
                if code1sum.has_key(str(v)):
                    tmp=[]
                    for i in range(len(code1sum[str(1)])):
                        n = code1sum[str(v)][i] + str2list[k][i]
                        tmp.append(n)
                    code1sum[str(v)] = tmp

                else:
                    code1sum[str(v)] = str2list[k]
                del unique[k]
        if code1sum:
            x, y, z = code1sum[str(1)][0], code1sum[str(1)][1], code1sum[str(1)][2]
            if z == 0:
                if x==1 and y==1:
                    unique[str(code1sum[str(1)])] = map_compressed_code[str(sum(code1sum[str(1)]))]
                elif x==0 and y==1:
                    unique[str(code1sum[str(1)])] = 2
                elif x==1 and y==0:
                    unique[str(code1sum[str(1)])] = 1
            else:
                return 'Error exists when doing comparison!!!!'
        codes=[]
        for k,v in unique.items():
            codes.append(v)
        m = min(codes)
        return(m)

    def adoptNremove(gff, old_p, new_p):
        new_ID = '{0:s}_{1:s}'.format(new_p['attributes']['ID'], old_p['attributes']['ID'])
        if new_p['attributes'].has_key('modified_track'):
            new_ID = '{0:s}_{1:s}'.format(new_p['attributes']['modified_track'], old_p['attributes']['ID'])
        elif old_p['attributes'].has_key('modified_track'):
            new_ID = '{0:s}_{1:s}'.format(new_p['attributes']['ID'], old_p['attributes']['modified_track'])
        new_p['attributes']['modified_track'] = new_ID

        gff.adopt(old_p, new_p)
        old_p['attributes']['modified_track'] = 'removed'

        for child in new_p['children']:
            fix_boundary(gff, child)
            #print(child['attributes']['ID'], child['attributes']['Parent'])

    def forfront(gff, p1, p2):
        len1 = p1['end'] - p1['start'] + 1
        len2 = p2['end'] - p2['start'] + 1
        if p1['start'] < p2['start']:
            adoptNremove(gff, p2, p1)
        elif p1['start'] > p2['start']:
            adoptNremove(gff, p1, p2)
        elif p1['start'] == p2['start']:
            if len1 >= len2:
                adoptNremove(gff, p2, p1)
            else:
                adoptNremove(gff, p1, p2)

    actions={'0':'printout', '1':'first', '2':'second', '3':'forfront'}
    gene1, gene2 = line['parents'], line2['parents']
    matrix=[]
    for parent1 in gene1:
        for p1 in parent1:
            vector1 = construct_vector(p1)
            for parent2 in gene2:
                for p2 in parent2:
                    if p1['attributes']['ID'] == p2['attributes']['ID']:
                        continue
                    vector2 = construct_vector(p2)
                    matrix = compare_vectors(vector1, vector2)
                    #print(matrix)
                    action_code = compress_matrix(matrix)

                    #print(action_code)
                    if p1['line_status'] == 'printout' or p2['line_status'] == 'printout':
                        action_code = 0
                    if actions[str(action_code)] == 'first':
                        adoptNremove(gff, p2, p1)
                    elif actions[str(action_code)] == 'second':
                        adoptNremove(gff, p1, p2)
                    elif actions[str(action_code)] == 'forfront':
                        forfront(gff, p1, p2)
                    

               
    



            
def fix_phase(gff3, error_list, line_num_dict, logger):
    """
    Ema0006 : Wrong phase
    Esf0026 : Phase is not 0, 1, or 2, or not a valid integer
    Esf0027 : Phase is required for all CDS features 
    """
    CDS_list = []
    CDS_set = set()
    valid_CDS_phase = set([0,1,2])
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                for root in gff3.collect_roots(gff3.lines[remove_line-1]):
                    if root['type'] != 'CDS':
                        root['type'] == '.'
                    for child in gff3.collect_descendants(root):
                        if child['type'] == 'CDS':
                            if child['line_raw'] not in CDS_set:
                                CDS_list.append(child)
                                CDS_set.add(child['line_raw'])
                        else:
                            child['type'] == '.'
                    if len(CDS_list) != 0:
                        if CDS_list[0]['strand'] == '-':
                            sorted_CDS_list = sorted(CDS_list, key=lambda x: x['end'], reverse=True)
                        elif CDS_list[0]['strand'] == '+':
                            sorted_CDS_list = sorted(CDS_list, key=lambda x: x['start'])
                    if CDS_list[0]['line_index']+1 in error:
                        if 'Ema0006' in line_num_dict[CDS_list[0]['line_index']]:
                            phase = map(int,re.findall(r'\d',line_num_dict[CDS_list[0]['line_index']][0]))[1]
                        else:
                            phase = 0
                        gff3.lines[CDS_list[0]['line_index']]['phase'] = phase
                        
                    else:
                        phase = CDS_list[0]['phase']
                    for CDS in sorted_CDS_list:
                        if line['phase'] != phase:
                            gff3.lines[CDS['line_index']]['phase'] = phase
                        phase = (3 - ((line['end'] - line['start'] + 1 - phase) % 3)) % 3

                    

                      

def remove_line(gff3, error_list, logger):
    """
    Esf0016: ##sequence-region seqid may only appear once
    Esf0020: Version is not a valid integer
    Esf0021: Inknown directive
    Esf0013: White chars not allowed at the start of a line
    """
    for error in error_list:
        for line_num in error:
            gff3.lines[remove_line-1]['line_status'] = 'removed'

def remove_attribute(gff3, error_list, logger):
    """
    Esf0030: Empty attribute tag
    Esf0031: Empty attribute value
    """
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                try:
                    attribute_dict = gff3.lines[remove_line-1]['attributes'].copy()
                    for tag, value in attribute_dict.items():
                        if not tag or not value.strip():
                            del gff3.lines[remove_line-1]['attributes'][tag]
                except:
                    logger.warning('[Missing Attribute] - Line (%s)', str(remove_line))


def add_gff3_version(gff3, logger):
    """
    Esf0014 : ##gff-version missing from the first line
    """
    # 
    line_data = {
                'line_index': 0,
                'line_raw': '##gff-version 3',
                'line_status': 'normal',
                'parents': [],
                'children': [],
                'line_type': 'directive',
                'directive': '##gff-version',
                'line_errors': [],
                'type': '',
                'version': 3
            }

    gff3.lines.insert(0, line_data)    

def replace_comma(gff3, error_list, logger):
    '''
    Esf0033 : Found "," in a attribute, possible unescaped
    Esf0036 : Value of a attribute contains unescaped ","
    '''
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                try:
                    attribute_dict = gff3.lines[remove_line-1]['attributes'].copy()
                    for tag, value in attribute_dict.items():
                        if ',' in tag or ',' in value:
                            del gff3.lines[remove_line-1]['attributes'][tag]
                            tag = tag.replace(',','%2C')
                            value = value.replace(',','%2C')
                            
                            gff3.lines[remove_line -1]['attributes'][tag] = value                            
                except:
                    logger.warning('[Missing Attribute] - Line (%s)', str(remove_line))

def remove_duplicate_attr(gff3, error_list, logger):
    '''
    Esf0034 : attribute has identical values (cound,value)
    '''
    from collections import OrderedDict
    multi_value_attributes = set(['replace','Parent', 'Alias', 'Dbxref', 'Ontology_term'])
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                try:
                    attribute_dict = gff3.lines[remove_line-1]['attributes'].copy()
                    for tag, value in attribute_dict.items():
                        if tag in multi_value_attributes:
                            gff3.lines[remove_line -1]['attributes'][tag] = list(OrderedDict.fromkeys(value))
                except:
                    logger.warning('[Missing Attribute] - Line (%s)', str(remove_line))
def unknown_reserved_attribute(gff3, error_list, logger):
    '''
    Esf0041 : Unknow reserved (uppercase) attribute
    '''
    reserved_attributes = set(['replace','ID', 'Name', 'Alias', 'Parent', 'Target', 'Gap', 'Derives_from', 'Note', 'Dbxref', 'Ontology_term', 'Is_circular'])
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                try:
                    attribute_dict = gff3.lines[remove_line-1]['attributes'].copy()
                    for tag, value in attribute_dict.items():
                        if tag not in reserved_attributes and tag[0].isupper():                           
                            del gff3.lines[remove_line-1]['attributes'][tag]
                            tag = tag[0].upper() + tag[1:] 
                            gff3.lines[remove_line -1]['attributes'][tag] = value
                except:
                    logger.warning('[Missing Attribute] - Line (%s)', str(remove_line))

def fix_attributes(gff3, error_list, logger):
    unescaped_field = re.compile(r'[\x00-\x1f\x7f]|%(?![0-9a-fA-F]{2})').search
    multi_value_attributes = set(['replace', 'Parent', 'Alias', 'Note', 'Dbxref', 'Ontology_term'])
    reserved_attributes = set(['replace','ID', 'Name', 'Alias', 'Parent', 'Target', 'Gap', 'Derives_from', 'Note', 'Dbxref', 'Ontology_term', 'Is_circular'])
    for error in error_list:
        for line_num in error:
            if gff3.lines[remove_line-1]['line_status'] != 'removed':
                tokens = map(str.strip, gff3.lines[remove_line-1]['line_raw'].split('\t'))
                if unescaped_field(tokens[8]):
                    # don't know how to fix this
                    pass
                attribute_tokens = tuple(tuple(t for t in a.split('=')) for a in tokens[8].split(';') if a)
                fixed_attributes = {}
                if len(attribute_tokens) == 1 and len(attribute_tokens[0]) == 1 and attribute_tokens[0][0] == '.':
                    pass # no attributes
                else:
                    for a in attribute_tokens:
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
                                    fixed_attributes[tag] + '%2C' + value
                            else:
                                if value in fixed_attributes[tag]:
                                    continue
                                else:
                                    fixed_attributes[tag]append(value)
                        if tag in multi_value_attributes:
                            if value.find(', ') >= 0 or value.find(' ,') >= 0:
                                value = value.replace(', ', '%2C')
                                value = value.replace(' ,', '%2C')
                            if tag in fix_attributes:
                                if tag == 'Note': # don't check for duplicate notes
                                    continue
                                else:
                                    fix_attributes[tag].extend([s for s in value.split(',') if s not in fix_attributes[tag]])
                            else:
                                fix_attributes[tag] = value.split(',')
                            # check for duplicate values
                            if tag != 'Note' and len(fix_attributes[tag]) != len(set(fix_attributes[tag])):
                                count_values = [(len(list(group)), key) for key, group in groupby(sorted(fix_attributes[tag]))]
                                # remove duplicate
                                fix_attributes[tag] = list(set(fix_attributes[tag]))
                        elif tag == 'Target':
                            if value.find(',') >= 0:
                                value = value.replace(',','%2C')
                            target_tokens = value.split(' ')
                            fix_attributes[tag] = {}
                            try:
                                fix_attributes[tag]['target_id'] = target_tokens[0]
                                all_good = True
                                try:
                                    fix_attributes[tag]['start'] = int(target_tokens[1])
                                except ValueError:
                                    all_good = False
                                    fix_attributes[tag]['start'] = target_tokens[1]
                                try:
                                    fix_attributes[tag]['end'] = int(target_tokens[2])
                                except ValueError:
                                    all_good = False
                                    fix_attributes[tag]['end'] = target_tokens[2]
                                # if all_good then both start and end are int, so we can check if start is not less than or equal to end
                                fix_attributes[tag]['strand'] = target_tokens[3]
                            except IndexError:
                                pass
                        else:
                            if value.find(',') >= 0:
                                value = value.replace(',','%2C')
                            if tag[:1].isupper() and tag not in reserved_attributes:
                                tag = tag[0].upper() + tag[1:]
                gff3.lines[remove_line-1]['attributes'] = fix_attributes
                            

def main(gff3=gff3, output_gff=args.out_gff, report=args.report, error_dict=error_dict, line_num_dict=line_num_dict, logger=None):
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
                delete_model(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Emr0001':
                remove_duplicate_trans(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Esf0020', 'Esf0016', 'Esf0021', 'Esf0013']:
                remove_line(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Esf0001','Ema0005']:
                pseudogene(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Ema0001', 'Ema0003']:
                fix_boundary(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Ema0006','Esf0027','Esf0026']:
                fix_phase(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code in ['Esf0030','Esf0031','Esf0029','Esf0034','Esf0041','Esf0032','Esf0028','Esf0036','Esf0033']:
                fix_attributes(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Ema0009':
                split(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Emr0002':
                merge(gff3=gff3, error_list=error_dict[error_code], logger=logger)
            elif error_code == 'Esf0014':
                add_gff3_version(gff3=gff3)
            gff3.write(output_gff)

            



