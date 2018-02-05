#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
# Copyright (C) 2015 Mei-Ju May Chen <arbula [at] gmail [dot] com>

"""

Changelog:
"""
from __future__ import print_function
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
import re
import copy
import logging
logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

def main(gff_object, error_object, error2fix):
    fixaction = FixAction(error2fix=error2fix)
    for line in gff_object.lines:
        if line['line_type'] == 'feature' and line['attributes'].has_key('ID'):
            if error_object.tid2error.has_key(line['attributes']['ID']):
                tid = line['attributes']['ID']
                errors = error_object.tid2error[tid]
                actions = {}
                for error in errors:
                    for k,v in fixaction.error2action.items():
                        if re.search(k, error): # set priority of fix actions
                            if v == 'delete_model': # the highest priority.
                                actions[v] = 0
                            elif v == 'merge':
                                continue
                            else:
                                actions[v] = 1
                if not actions == {}:
                    actions_sorted = sorted(actions, key=lambda i: int(actions[i]))
                    flag = 0
                    for i in actions_sorted:
                        method = getattr(fixaction, i)
                        if not method:
                            raise Exception("Method %s not implemented" % i)
                        if flag == 0:
                            print(tid, i, actions[i])
                            if i == 'merge': # Inputs for merge function are different from other methods
                                line2 = {}
                                for error in errors:
                                    if re.search('wrongly split gene parent', error):
                                        IDs = re.search('wrongly split gene parent\? (\S+) and (.+?)]', error)
                                        for ID in IDs.groups():
                                            if not ID == tid:
                                                sline = [tline for tline in gff_object.lines if tline['line_type']=='feature' and tline['attributes']['ID'] == ID]
                                                line2 = sline[0]
                                print(line['attributes']['Parent'], line2['attributes']['Parent'])
                                method(gff_object, line, line2)
                            else:
                                method(gff_object, line)
                            if actions[i] == 0:
                                flag += 1
        elif line['line_type'] == 'feature' and not line['attributes'].has_key('ID'):
            #print(line['type'])
            pass

    for line in gff_object.lines:
        if line['line_type'] == 'feature' and line['attributes'].has_key('ID'):
            if error_object.tid2error.has_key(line['attributes']['ID']):
                tid = line['attributes']['ID']
                errors = error_object.tid2error[tid]
                actions = {}
                for error in errors:
                    for k,v in fixaction.error2action.items():
                        if re.search(k, error): # set priority of fix actions
                            if v == 'merge': # the highest priority.
                                actions[v] = 0
                if not actions == {}:
                    actions_sorted = sorted(actions, key=lambda i: int(actions[i]))
                    flag = 0
                    for i in actions_sorted:
                        method = getattr(fixaction, i)
                        if not method:
                            raise Exception("Method %s not implemented" % i)
                        if flag == 0:
                            print(tid, i, actions[i])
                            if i == 'merge': # Inputs for merge function are different from other methods
                                line2 = {}
                                for error in errors:
                                    if re.search('wrongly split gene parent', error):
                                        IDs = re.search('wrongly split gene parent\? (\S+) and (.+?)]', error)
                                        for ID in IDs.groups():
                                            if not ID == tid:
                                                sline = [tline for tline in gff_object.lines if tline['line_type']=='feature' and tline['attributes'].has_key('ID') and tline['attributes']['ID'] == ID]
                                                line2 = sline[0]
                                print(line['attributes']['Parent'], line2['attributes']['Parent'])
                                method(gff_object, line, line2)
                            else:
                                method(gff_object, line)
                            if actions[i] == 0:
                                flag += 1

class FixAction(object):
    """
    A class collects all actions for different errro types. The input file of [error2fix] must include fix method name after a '>' and the corresponding error tags that need to be fixed listed below the line of '>'. If you would like not perform a specific action, you could just comment (by using '#') that specific action or error to silencing the action.
    """
    def __init__(self, error2fix=None):
        self.error2action = {}
        if error2fix:
            self.mapError2Action(error2fix)

    def mapError2Action(self, error2fix):
        error2action={}
        action = ''
        for line in open(error2fix, 'rb'):
            line = line.rstrip('\n')
            if line.startswith(r"#"):
                continue
            if line.startswith(r">"):
                line = re.sub(r'>', r'', line)
                action = line
            else:
                error2action[line]=action
        self.error2action = error2action

    def connected_compoents(self, child_list, pair_list):
        # The graph nodes.
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
            # Iterate while we still have nodes to process.
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
        nodes = set()
        for v in nodelist.itervalues():
            nodes.add(v)
        result = []
        for components in cc(nodes):
            names = sorted(node.name for node in components)
            result.append(names)
        return result

    def delete_model(self, gff, line):
        """
        Delete models containing the following errors,
            Negative start/end coordinate
            Zero start coordinate
        """
        gff.remove(line)
        parents = line['parents']
        for parent in parents:
            for p in parent:
                p['attributes']['modified_track'] = 'removed'
                p['line_status'] = 'normal'

    def fix_boundary(self, gff, mRNAline):
        """
        Fix the gene boundary for the follwoing errors,
            redundant length of the gene
            A child feature over a coordinate boundary of its related gene
            BOUNDS: This feature is not contained within the feature boundaries of parent
        """
        line = mRNAline
        parents = line['parents']
        for parent in parents:
            for p in parent:
                cPos = []
                for child in p['children']:
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
                p['start'] = minc
                p['end'] = maxc
                #p['attributes']['modified_track'] = 'fix_boundary'

    def pseudogene(self, gff, line):
        """
        Fix: 1) change mRNA to pseudogenic_transcript; change exon to pseudogenic_exon; remove CDS lines
            mRNA in the type of pseudogene found
            pseudogene or not?
        """
        parents = line['parents']
        for parent in parents:
            for p in parent:
                if p['type'] == 'gene':
                    p['type'] = 'pseudogene'
                for child in p['children']:
                    if child['type'] == 'mRNA' or child['type'] == 'transcript':
                        child['type'] = 'pseudogenic_transcript'
                    for grandchild in child['children']:
                        if grandchild['type'] == 'CDS':
                            grandchild['line_status'] = 'removed'
                        elif grandchild['type'] == 'exon':
                            grandchild['type'] = 'pseudogenic_exon'
                #p['attributes']['modified_track'] = 'pseudogene'

    def split(self, gff, line):
        """
        Split wrongly merged models.
            Visit all children of the gene, and decide which mRNAs should be seperated from the origial model (Reprogramming!!). Split before merge?
        """
        if line['line_status'] == 'split':
            return 1
        eofindex = len(gff.lines)-1

        parents = line['parents']
        for parent in parents:
            for p in parent:
                oldID = p['attributes']['ID']
                old_feature = gff.features[oldID]
                if p['attributes'].has_key('modified_track') and p['attributes']['modified_track'] == 'removed':
                    continue

                # find the children that need to be seperated.
                children = p['children']
                hitpair=[]
                childrenlist=[]
                for i in range((len(children)-1)):
                    c1 = children[i]
                    childrenlist.append(c1['attributes']['ID'])
                    for j in range((i+1), (len(children))):
                        c2 = children[j]
                        hit = 0
                        if gff.overlap(c1, c2):
                            gchildren1 = c1['children']
                            gchildren2 = c2['children']
                            for gc1 in gchildren1:
                                for gc2 in gchildren2:
                                    if gff.overlap(gc1, gc2):
                                        hit += 1
                        if hit > 0:
                            pair = ' '.join([c1['attributes']['ID'], c2['attributes']['ID']])
                            hitpair.append(pair)
                            print('Hit_pair:', c1['attributes']['ID'], c2['attributes']['ID'], hit)
                childrenlist.append(children[(len(children)-1)]['attributes']['ID'])
                childgroup = self.connected_compoents(childrenlist, hitpair)
                flag = 1
                for i in range(len(childgroup)):
                    # new a novel gene parent, fix line_index, adopt one of the mRNAs of the original model, add new gene parent to gff.features and gff.lines
                    newID=''
                    if p['attributes'].has_key('modified_track'):
                        newID = '{0:s}.s{1:d}'.format(p['attributes']['modified_track'], flag)
                    else:
                        newID = '{0:s}.s{1:d}'.format(oldID, flag)
                    newparent = copy.deepcopy(p)
                    newparent['attributes']['ID'] = newID
                    if newparent['attributes']['Name'] == newparent['attributes']['ID']:
                        newparent['attributes']['Name'] = newID
                    eofindex += 1
                    newparent['line_index'] = eofindex
                    newparent['children']=[]
                    print('group', i, ':', childgroup[i])
                    for j in childgroup[i]:
                        children = gff.features[j]
                        for child in children:
                            newparent['children'].append(child)
                    newparent['attributes']['modified_track'] = newID
                    gff.features[newID].append(newparent)
                    gff.lines.append(newparent)
                    # update the child's parent list and parent attribute
                    for j in childgroup[i]:
                        children = gff.features[j]
                        for child in children:
                            child['parents'] = []
                            child['parents'].append(gff.features[newID])
                            child['attributes']['Parent']=[]
                            child['attributes']['Parent'].append(newID)
                            child['line_status'] = 'split'
                            # make gene boundary to go with mRNA boundary
                            self.fix_boundary(gff, child)
                    print(i, p['attributes']['ID'], child['attributes']['ID'],gff.lines[(len(gff.lines)-1)]['attributes']['ID'], gff.lines[(len(gff.lines)-1)]['line_index'])
                    flag += 1
                # remove the old model's children list and then remove the old model
                for old_ld in old_feature:
                    old_ld['children'] = []
                p['attributes']['modified_track'] = 'removed'


    def merge(self, gff, line, line2):
        """
        Merge wrongly split model
        """
        def construct_vector(line):
            name_field=['Name']
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
                self.fix_boundary(gff, child)
                print(child['attributes']['ID'], child['attributes']['Parent'])

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
                        print('IDs:', p1['attributes']['ID'], p2['attributes']['ID'])
                        print(vector1)
                        print(vector2)
                        print(matrix)
                        action_code = compress_matrix(matrix)
                        print(action_code)
                        if p1['line_status'] == 'printout' or p2['line_status'] == 'printout':
                            action_code = 0
                        if actions[str(action_code)] == 'first':
                            adoptNremove(gff, p2, p1)
                        elif actions[str(action_code)] == 'second':
                            adoptNremove(gff, p1, p2)
                        elif actions[str(action_code)] == 'forfront':
                            forfront(gff, p1, p2)
                        else:
                            print(p1['attributes']['ID'], vector1)
                            print(p2['attributes']['ID'], vector2)


class Gff3error(object):
    def __init__(self, error_report=None, logger=logger):
        self.logger = logger
        self.tid2error = {}
        self.tid2info = {}
        if error_report:
            self.erparse(error_report)

    def erparse(self, error_report):
        """
        Parse internal validation report to a dictionary preserving transcript ID -> errors.
        """
        column = ['transcript_id','automated_issue_tracker']
        column2curator = ['gene_id', 'transcript_id', 'transcript_owner', 'gene_name', 'transcript_name', 'transcript_scaffold', 'transcript_start', 'transcript_end', 'transcript_strand', 'transcript_type', 'transcript_Replaced_model', 'transcript_URL', 'automated_issue_tracker']
        colid = []
        colid2 = []
        tid2error = {}
        tid2info = {}
        flag = 0
        for line in open(error_report, 'rb'):
            line = line.rstrip('\n')
            t = line.split('\t')
            if flag == 0:
                for i in column:
                    for j in range(len(t)):
                        if t[j] == i:
                            colid.append(j)
                for i in column2curator:
                    for j in range(len(t)):
                        if t[j] == i:
                            colid2.append(j)
            if flag > 0:
                tokens = t[colid[1]].split('; ')
                if not tokens[0] == 'NA':
                    tid2error[t[colid[0]]] = tokens
                    info = []
                    for i in colid2[2:]:
                        info.append(t[i])
                    tid2info[t[colid[0]]] = line
            flag += 1
        self.tid2error = tid2error
        self.tid2info = tid2info
        return 1
