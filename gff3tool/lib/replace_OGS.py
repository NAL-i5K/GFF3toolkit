from __future__ import print_function
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
import sys
import re
import string
import logging
from gff3tool.lib import id_processor

logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

def featureSort(linelist, reverse=False):
    FEATURECODE = {
        'gene': 0,
        'pseudogene': 0,
        'mRNA': 1,
        'pseudogenic_transcript': 1,
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
    newlinelist = []
    for k in keys:
        ids = seq2id[k]
        d = {}
        for ID in ids:
            d[ID] = id2index[ID]
        id_sorted = sorted(d, key=lambda i: (int(d[i][0]), int(d[i][1])), reverse=reverse)
        for i in id_sorted:
            newlinelist.append(id2line[i])
    return newlinelist


def merge(gff, line, line2, oID):
    """
    Merge wrongly split model
    """

    def fix_boundary(gff, mRNAline):
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
                return 'Warning exists when doing comparison!!!!'
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
        old_p['line_status'] = 'removed'

        for child in new_p['children']:
            fix_boundary(gff, child)
            #print(child['attributes']['ID'], child['attributes']['Parent'])

    def forfront(gff, p1, p2): # Select the gene that has smaller genomic coordinate
        len1 = p1['end'] - p1['start'] + 1
        len2 = p2['end'] - p2['start'] + 1
        pinfo = str()
        if p1['start'] < p2['start']:
            adoptNremove(gff, p2, p1)
            pinfo = "{0:s} ({1:s})".format(p1['attributes']['ID'], "action_type:smaller genomic coordinate")
        elif p1['start'] > p2['start']:
            adoptNremove(gff, p1, p2)
            pinfo = "{0:s} ({1:s})".format(p2['attributes']['ID'], "action_type:smaller genomic coordinate")
        elif p1['start'] == p2['start']:
            if len1 >= len2:
                adoptNremove(gff, p2, p1)
                pinfo = "{0:s} ({1:s})".format(p1['attributes']['ID'], "action_type:smaller genomic coordinate")
            else:
                adoptNremove(gff, p1, p2)
                pinfo = "{0:s} ({1:s})".format(p2['attributes']['ID'], "action_type:smaller genomic coordinate")

    actions={'0':'printout', '1':'first', '2':'second', '3':'forfront'}
    p1, p2 = line, line2
    matrix=[]
    report = []
    vector1 = construct_vector(p1)
    if p1['attributes']['ID'] == p2['attributes']['ID']:
        return(report)
    vector2 = construct_vector(p2)
    matrix = compare_vectors(vector1, vector2)
    #report.extend(["# {0:s} {1:s} {2:s}\n".format('IDs:', p1['attributes']['ID'], p2['attributes']['ID'])])
    #report.extend(matrix)
    action_code = compress_matrix(matrix)
    #report.append("Action_code:\t{0:s}".format(action_code))
    pinfo = str()
    if p1['line_status'] == 'printout' or p2['line_status'] == 'printout':
        action_code = 0
    if actions[str(action_code)] == 'first':
        adoptNremove(gff, p2, p1)
        pinfo="{0:s} ({1:s})".format(p2['attributes']['ID'], "action_type:first")
    elif actions[str(action_code)] == 'second':
        adoptNremove(gff, p1, p2)
        pinfo="{0:s} ({1:s})".format(p2['attributes']['ID'], "action_type:second")
    elif actions[str(action_code)] == 'forfront':
        pinfo=forfront(gff, p1, p2)
    else:
        report.extend(["#[Warning] Please adapt the column 9 information of the two genes below."])
        report.extend(["#\t\t- {0:s}: {1:s}".format(p1['attributes']['ID'],str(vector1))])
        report.extend(["#\t\t- {0:s}: {1:s}".format(oID, str(vector2))])


    if len(pinfo)>0:
        report.insert(0, "{0:s} (primary gene)".format(pinfo))
    return(report)


class Groups(object):

    def __init__(self, WAgff=None, Pgff=None, outsideNum=int, user_defined1=None, user_defined2=None, logger=logger):
        self.logger = logger
        self.WAgff = WAgff
        self.Pgff = Pgff
        self.user_defined1 = user_defined1
        self.user_defined2 = user_defined2
        self.outsideNum = outsideNum
        self.mapType2Log = {'simple':'replaced by WA model: simple replacement','merge':'replaced by WA model: merge','split':'replaced by WA model: split','add':'newly added WA model: add','other':'no change', 'Delete':'removed', 'multi-ref':'replaced by WA model: deal with reference gene with multiple transcripts'}

        self.mapName2ID = {}
        self.idprefix = str
        self.maxIDnumber = int
        self.digitlen = int
        self.info = []
        self.id2name = {}
        if Pgff:
            self.name2id(Pgff, user_defined2)
        if WAgff:
            self.grouping(WAgff, user_defined1)

    def grouping(self, WAgff, user_defined1):
        u_type = set()
        if user_defined1 != None:
            for line in user_defined1:
                u_type.add(line[0])

        roots = []
        transcripts = []
        unique = set()
        for line in WAgff.lines:
            if user_defined1 is None:
                try:
                    if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                        roots.append(line)
                except:
                    pass
            else:
                if line['type'] in u_type:
                    transcripts.append(line)
                    for root in WAgff.collect_roots(line):
                        if root['line_raw'] not in unique:
                            roots.append(root)
                            unique.add(root['line_raw'])

        #roots = [line for line in WAgff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
        uniqueReplaceID = {}
        for root in roots:
            if user_defined1 is None:
                children = root['children']
            else:
                children = []
                if root['type'] in u_type:
                    children.append(root)
                else:
                    for child in WAgff.collect_descendants(root):
                        if child['type'] in u_type:
                            children.append(child)
                children = sorted(children, key=lambda k: k['line_index'])
            for child in children:
                child['attributes']['replace'].sort()
                if len(child['attributes']['replace']) == 1 and child['attributes']['replace'][0] == 'NA':
                    if user_defined1 is None:
                        parent = child['parents']
                        childrtag = {}
                        for parent_lines in parent:
                            for line in parent_lines:
                                tmpchildren = line['children']
                                for tmpchild in tmpchildren:
                                    tmpline = ','.join(tmpchild['attributes']['replace'])
                                    childrtag[tmpline] = 0
                    else:
                        childrtag = {}
                        for line in WAgff.collect_roots(child):
                            tmpchildren = []
                            if line['type'] in u_type:
                                tmpchildren.append(line)
                            else:
                                for tmpchild in WAgff.collect_descendants(line):
                                    if tmpchild['type'] in u_type:
                                        tmpchildren.append(tmpchild)
                            tmpchildren = sorted(tmpchildren, key=lambda k: k['line_index'])
                            for tmpchild in tmpchildren:
                                tmpline = ','.join(tmpchild['attributes']['replace'])
                                childrtag[tmpline] = 0

                    if len(childrtag) == 1:
                        pass
                    elif len(childrtag) == 2:
                        # If a gene contains multiple transcripts, and one of them is 'NA' and the others belong to a specific reference transcript. Then, replace 'NA' with that specific refernece transcript.
                        for tmptag in childrtag:
                            if not tmptag == 'NA':
                                tmplist = tmptag.split(',')
                                child['attributes']['replace'] = tmplist
                    else:
                            # The case cannot be processed.
                        print('Warning -- inconsitent replace tags, one is NA: {0:s}'.format(child['attributes']['ID']))

                rIDs = child['attributes']['replace']
                for i in rIDs:
                    if (uniqueReplaceID.has_key(i)):
                        uniqueReplaceID[i].append(child)
                    else:
                        uniqueReplaceID[i] = []
                        uniqueReplaceID[i].append(child)

        for k, v in uniqueReplaceID.items():
            parents = {} # for each replace tag, all the gene IDs involved.
            for i in v:
                if user_defined1 is None:
                    parent = i['parents']
                    for parent_lines in parent:
                        for line in parent_lines:
                            parents[line['attributes']['ID']]=0
                else:
                    parent = WAgff.collect_roots(i)
                    for line in parent:
                        parents[line['attributes']['ID']]=0

            for i in v:
                if k == 'NA':
                    if user_defined1 is None:
                        parent = i['parents']
                        childrtag = {}
                        for parent_lines in parent:
                            for line in parent_lines:
                                tmpchildren = line['children']
                                for tmpchild in tmpchildren:
                                    childrtag[str(tmpchild['attributes']['replace'])] = 0
                    else:
                        childrtag = {}
                        for line in WAgff.collect_roots(i):
                            tmpchildren = []
                            if line['type'] in u_type:
                                tmpchildren.append(line)
                            else:
                                for tmpchild in WAgff.collect_descendants(line):
                                    if tmpchild['type'] in u_type:
                                        tmpchildren.append(tmpchild)
                            tmpchildren = sorted(tmpchildren, key=lambda kid: kid['line_index'])
                            for tmpchild in tmpchildren:
                                childrtag[str(tmpchild['attributes']['replace'])] = 0
                    if len(childrtag) == 1:
                        i['attributes']['replace_type'] = 'add'
                    else:
                        i['attributes']['replace_type'] = 'manual ({0:s})'.format(i['attributes']['ID'])
                elif len(v) == 1:
                    if len(i['attributes']['replace']) == 1:
                        i['attributes']['replace_type'] = 'simple'
                    else:
                        i['attributes']['replace_type'] = 'merge'
                else:
                    if len(parents) == 1:
                        if len(i['attributes']['replace']) == 1:
                            i['attributes']['replace_type'] = 'simple'
                        else:
                            i['attributes']['replace_type'] = 'merge'
                    else:
                        i['attributes']['replace_type'] = 'split'
            '''
            print(k, len(v))
            for i in v:
                print("  Detail:", i['attributes']['replace_type'], i['attributes']['replace'])
            '''

        for root in roots:
            if user_defined1 is None:
                children = root['children']
            else:
                children = []
                if root['type'] in u_type:
                    children.append(root)
                else:
                    for child in WAgff.collect_descendants(root):
                        if child['type'] in u_type:
                            children.append(child)
                children = sorted(children, key=lambda k: k['line_index'])

            rtypes={}
            rtags={}
            for child in children:
                rtypes[child['attributes']['replace_type']] = 0
                for tag in child['attributes']['replace']:
                    rtags[tag] = 0
            if len(rtypes) == 1:
                for k, v in rtypes.items():
                    root['attributes']['replace_type'] = k
                tmp = []
                for k, v in rtags.items():
                    tmp.append(k)
                root['attributes']['replace'] = tmp
            elif len(rtypes) == 0:
                root['attributes']['replace_type'] = 'add'
                root['attributes']['replace'] = ['NA']
            else:
                print('Warning! Two or more replace types for a gene model: {0:s}. This gene model is not processed!'.format(root['attributes']['ID']))
                root['attributes']['replace_type'] = 'internal_review'
        for root in roots:
            if user_defined1 is None:
                children = root['children']
            else:
                children = []
                if root['type'] in u_type:
                    children.append(root)
                else:
                    for child in WAgff.collect_descendants(root):
                        if child['type'] in u_type:
                            children.append(child)
                children = sorted(children, key=lambda k: k['line_index'])

            for child in children:
                if child['attributes'].has_key('status') and (child['attributes']['status'] == 'Delete' or child['attributes']['status'] == 'delete'):
                    child['attributes']['replace_type'] == 'Delete'
                    if user_defined1 is None:
                        for p_line in child['parents']:
                            for p in p_line:
                                p['attributes']['replace_type'] == 'Delete'
                    else:
                        for p in WAgff.collect_roots(child):
                            p['attributes']['replace_type'] == 'Delete'


    def name2id(self, Mgff, user_defined2=None):
        u_types = set()
        if user_defined2 is not None:
            for line in user_defined2:
                u_types.add(line[0])
        roots = []
        transcripts = []
        unique = set()
        for line in Mgff.lines:
            if user_defined2 is None:
                try:
                    if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                        roots.append(line)
                except:
                    pass
            else:
                if line['type'] in u_types:
                    transcripts.append(line)
                    for root in Mgff.collect_roots(line):
                        if root['line_raw'] not in unique:
                            roots.append(root)
                            unique.add(root['line_raw'])
        #roots = [line for line in Mgff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
        mapName2ID = {}
        tmp  = re.search('(.+?)(\d+)',roots[0]['attributes']['ID'])
        idprefix = tmp.groups()[0]
        maxIDnumber = 0
        digitlen = 0
        id2name={}
        for root in roots:
            rootid = root['attributes']['ID']
            if root['attributes'].has_key('Name'):
                id2name[rootid] = root['attributes']['Name']
                #substring = re.search('(\d+)', rootid)
                #if re.search(substring.groups()[0], root['attributes']['Name']):
                    #root['attributes']['Name'] = rootid
            #if re.search(idprefix, rootid):
                #tmp = re.search('(.+?)(\d+)',rootid)
                #IDnumber = tmp.groups()[1]
                #digitlen = len(IDnumber)
                #if int(IDnumber) > maxIDnumber:
                    #maxIDnumber = int(IDnumber)
            if user_defined2 is None:
                children = root['children']
            else:
                children = []
                if root['type'] in u_types:
                    children.append(root)
                else:
                    for child in Mgff.collect_descendants(root):
                        if child['type'] in u_types:
                            children.append(child)
                children = sorted(children, key=lambda k: k['line_index'])
            for child in children:
                if child['attributes'].has_key('Name'):
                    mapName2ID[child['attributes']['Name']] = child['attributes']['ID']
                mapName2ID[child['attributes']['ID']] = child['attributes']['ID']
                if child['attributes'].has_key('Name'):
                    id2name[child['attributes']['ID']]=child['attributes']['Name']
                else:
                    id2name[child['attributes']['ID']]=child['attributes']['ID']
                    #substring = re.search('(\d+)', child['attributes']['ID'])
                    #if re.search(substring.groups()[0], child['attributes']['Name']):
                        #child['attributes']['Name'] = child['attributes']['ID']
                gchildren = child['children']
                calexon = 0
                for gchild in gchildren:
                    otherlines = []
                    if gchild['type'] == 'exon':
                        exonnum = id_processor.idgenerator('EXON', calexon, 2)
                        pids = {}
                        for pid in gchild['attributes']['Parent']:
                            pids['{0:s}-{1:s}'.format(pid, exonnum['ID'])]=1
                        pidline = []
                        for k,v in pids.items():
                            pidline.append(k)
                        newid = ','.join(pidline)
                        calexon = exonnum['maxnum']
                        #self.replaceIDName(gchild, newid)
                    else:
                        pids = {}
                        for pid in gchild['attributes']['Parent']:
                            pids['{0:s}-{1:s}'.format(pid, gchild['type'])]=1
                        pidline = []
                        for k,v in pids.items():
                            pidline.append(k)
                        #gchild['attributes']['ID'] = ','.join(pidline)
                    otherlines.extend(Mgff.collect_descendants(gchild))

                    #for k in otherlines:
                        #if k['attributes'].has_key('ID'):
                            #for p in k['parents']:
                                #newid = p[-1]['attributes']['ID'] + '-' + k['type']
                                #self.replaceIDName(k, newid)
                                #k['attributes']['Parent'] = p[-1]['attributes']['ID']
                                #print ('[renameID]',str(k['attributes']['Parent']), k['attributes']['ID'], p[-1]['attributes']['ID'])


        self.mapName2ID = mapName2ID
        self.idprefix = idprefix
        if (maxIDnumber > self.outsideNum):
            self.maxIDnumber = maxIDnumber
        else:
            self.maxIDnumber = self.outsideNum
        self.digitlen = digitlen
        self.id2name = id2name

    def replaceIDName (self, line_data, newid):
        if line_data['attributes'].has_key('Name') and (re.search(r'\[', line_data['attributes']['Name']) or re.search(r'\]', line_data['attributes']['Name'])):
           line_data['attributes']['Name'] = re.sub(r'\[', r'(', line_data['attributes']['Name'])
           line_data['attributes']['Name'] = re.sub(r'\]', r')', line_data['attributes']['Name'])
        if line_data['attributes'].has_key('Name') and re.search(line_data['attributes']['Name'], line_data['attributes']['ID']):
            #print('[Debug]', line_data['attributes']['ID'], line_data['attributes']['Name']) #debug

            line_data['attributes']['ID'] = newid
            line_data['attributes']['Name'] = newid
        else:
            line_data['attributes']['ID'] = newid
        return 1

    def renameID(self, line, tpid):
        parent = []
        if type(line) is not dict:
            return("[Warning] The line is not a dict structure!\t{0:s}".format(str(line)))
        if line['attributes'].has_key('Parent'):
            parent = line['parents'][0]
        else:
            parent = [line]

        for parent_line in parent:
            self.replaceIDName(parent_line, tpid)
            children = parent_line['children']
            maxindex = 0
            for child in children:
                newalphabet = string.uppercase[maxindex]
                newid = tpid + '-R' + newalphabet
                child['attributes']['Parent'] = [tpid]
                self.replaceIDName(child, newid)
                #print('-----', line['attributes']['ID'], child['attributes']['ID'], child['attributes']['replace'], '-----')
                maxindex += 1
                gchildren = child['children']
                calexon = 0
                for gchild in gchildren:
                    otherlines = []
                    gchild['attributes']['Parent'] = [child['attributes']['ID']]
                    if gchild['type'] == 'exon':
                        exonnum = id_processor.idgenerator('EXON', calexon, 2)
                        pids = {}
                        for pid in gchild['attributes']['Parent']:
                            pids['{0:s}-{1:s}'.format(pid, exonnum['ID'])]=1
                        pidline = []
                        for k,v in pids.items():
                            pidline.append(k)
                        newid = ','.join(pidline)
                        calexon = exonnum['maxnum']
                        self.replaceIDName(gchild, newid)
                    else:
                        newid = gchild['attributes']['Parent'][0] + '-' + gchild['type']
                        pids = {}
                        for pid in gchild['attributes']['Parent']:
                            pids['{0:s}-{1:s}'.format(pid, gchild['type'])]=1
                        pidline = []
                        for k,v in pids.items():
                            pidline.append(k)
                        newid = ','.join(pidline)
                        self.replaceIDName(gchild, newid)
                    otherlines.extend(self.WAgff.collect_descendants(gchild))

                    for k in otherlines:
                        if k['attributes'].has_key('ID'):
                            del k['attributes']['ID']
                            for p in k['parents']:
                                newid = p[-1]['attributes']['ID'] + '-' + k['type']
                                self.replaceIDName(k, newid)
                                k['attributes']['Parent'] = p[-1]['attributes']['ID']
                                print ('[renameID]',str(k['attributes']['Parent']), k['attributes']['ID'], p[-1]['attributes']['ID'])


    def newUTRfeature(self, fname, exonline, ID, gff):
        newf = id_processor.newChildModel(exonline, ID, gff)
        newf['parents'] = exonline['parents']
        newf['attributes']['Parent'] = exonline['attributes']['Parent']
        newf['type'] = fname
        newf['attributes']['ID'] = ID + '-' + fname
        newf['attributes']['Name'] = newf['attributes']['ID']
        gff.lines.append(newf)
        gff.features[newf['attributes']['ID']].append(newf)
        for parent in newf['parents']:
            for p in parent:
                p['children'].append(newf)
        return newf

    def gen5UTR(self, fname, cdsline, exonlist, ID, gff):
        #print('CDS: {0:s}'.format(cdsline['line_raw']))
        for exonline in exonlist:
            #print('Before: {0:s}'.format(exonline['line_raw']))
            if exonline['end'] < cdsline['start']:
                newf = self.newUTRfeature(fname, exonline, ID, gff)
                #print('After: {0:s}\t{1:s}\t{2:d}\t{3:d}\n'.format(newf['attributes']['ID'], newf['type'], newf['start'], newf['end']))
            elif (exonline['start'] - cdsline['start']) < 0:
                newf = self.newUTRfeature(fname, exonline, ID, gff)
                newf['end'] = cdsline['start']-1
                #print('After: {0:s}\t{1:s}\t{2:d}\t{3:d}\n'.format(newf['attributes']['ID'], newf['type'], newf['start'], newf['end']))
            else:
                pass

    def gen3UTR(self, fname, cdsline, exonlist, ID, gff):
        #print('CDS: {0:s}'.format(cdsline['line_raw']))
        for exonline in exonlist:
            #print('Before: {0:s}'.format(exonline['line_raw']))
            if exonline['start'] > cdsline['end']:
                newf = self.newUTRfeature(fname, exonline, ID, gff)
                #print('After: {0:s}\t{1:s}\t{2:d}\t{3:d}\n'.format(newf['attributes']['ID'], newf['type'], newf['start'], newf['end']))
            elif (exonline['end'] - cdsline['end']) > 0:
                newf = self.newUTRfeature(fname, exonline, ID, gff)
                newf['start'] = cdsline['end']+1
                #print('After: {0:s}\t{1:s}\t{2:d}\t{3:d}\n'.format(newf['attributes']['ID'], newf['type'], newf['start'], newf['end']))
            else:
                pass

    def replacer_add(self, line, RG, Mgff):
        lparent = line
        if not lparent['attributes'].has_key('modified_track'):
            newID = {}
            newID['ID'] = lparent['attributes']['ID']
            newID['maxnum'] = RG.maxIDnumber

            RG.maxIDnumber = newID['maxnum']
            # New model with replaced information in predicted gff
            #self.renameID(lparent, newID['ID'])
            id_processor.general_newModel(lparent, Mgff)
            '''
            # Generate utr features for each curated models
            t = Mgff.features[newID['ID']][0]
            if t.has_key('children'):
                tchildren = t['children']
                for tchild in tchildren:
                    if tchild.has_key('children'):
                        tgchildren = tchild['children']
                        linelist = []
                        for tgchild in tgchildren:
                            if tgchild['type'] == 'exon' or tgchild['type'] == 'CDS':
                                linelist.append(tgchild)

                        sortedlines = featureSort(linelist, False)
                        exonlist = []
                        CDSline = dict()
                        for eachline in sortedlines:
                            #print('[5UTR] {0:s}'.format(eachline['line_raw']))
                            if eachline['type'] == 'CDS':
                                CDSline = eachline
                                if len(exonlist) >= 1:
                                    featurename = str()
                                    if CDSline['strand'] == '+':
                                        featurename = 'five_prime_utr'
                                    elif CDSline['strand'] == '-':
                                        featurename = 'three_prime_utr'
                                    self.gen5UTR(featurename, CDSline, exonlist, tchild['attributes']['ID'], Mgff)
                                break
                            if eachline['type'] == 'exon':
                                exonlist.append(eachline)

                        exonlist=[]
                        sortedlines = featureSort(linelist, True)
                        for eachline in sortedlines:
                            #print('[3UTR] {0:s}'.format(eachline['line_raw']))
                            if eachline['type'] == 'CDS':
                                CDSline = eachline
                                if len(exonlist) >= 1:
                                    featurename = str()
                                    if CDSline['strand'] == '+':
                                        featurename = 'three_prime_utr'
                                    elif CDSline['strand'] == '-':
                                        featurename = 'five_prime_utr'
                                    self.gen3UTR(featurename, CDSline, exonlist, tchild['attributes']['ID'], Mgff)
                                break
                            if eachline['type'] == 'exon':
                                exonlist.append(eachline)

            '''
            # Final return
            return(newID)

    def replacer (self, line, RG, Mgff, u1_types=None, gff3=None):
        '''
        line should be root line.
        '''
        Name2ID = RG.mapName2ID
        rtags = line['attributes']['replace']
        originalID = line['attributes']['ID']
        targets = []
        mid = []
        newtarget=line

        if line['attributes']['replace_type'] == 'simple' and len(line['attributes']['replace']) > 1:
            print('Warning: Wrong grouping!!!! simple replacement with multiple replace tags! - ', line['attributes']['replace'], 'at', line['line_raw'])
            sys.exit()

        if line['attributes']['replace_type'] == 'add':
            if not line['attributes'].has_key('modified_track'):
                newid = self.replacer_add(line, RG, Mgff)
                newtarget = Mgff.features[newid['ID']][0]
                newtarget['attributes']['modified_track'] = '{0:s}:{1:s}'.format(line['attributes']['replace_type'], originalID)
                try:
                    self.info.append('{0:s}\t{1:s}\t{2:s}\t{3:s}'.format(originalID, newtarget['attributes']['ID'], newtarget['attributes']['replace'], newtarget['attributes']['modified_track']))
                except:
                    pass
        #elif line['attributes']['replace_type'] == 'simple': # Simple replacement for a model should inherite the original ID.
        #    if len(line['attributes']['replace']) > 1:
        #        print('Warning: Wrong grouping!!!! simple replacement with multiple replace tags! - ', line['attributes']['replace'], 'at', line['line_raw'])
        #        sys.exit()
        #    keepID = re.search('(.+?)-R.',Name2ID[line['attributes']['replace'][0]])
        #    if not line['attributes'].has_key('modified_track'):
        #        newid = self.replacer_add(line, RG, Mgff)
        #        self.renameID(Mgff.features[newid['ID']][0], keepID.groups()[0])
        #        newtarget = Mgff.features[newid['ID']][0]
        #        newtarget['attributes']['modified_track'] = '{0:s}:{1:s}'.format(line['attributes']['replace_type'], originalID)
        #        self.info.append('{0:s}\t{1:s}\t{2:s}\t{3:s}'.format(originalID, newtarget['attributes']['ID'], newtarget['attributes']['replace'], newtarget['attributes']['modified_track']))
                #print('simple_replacement: ',newid['ID'],keepID.groups()[0])
        #    Mgff.remove(Mgff.features[keepID.groups()[0]][0])

        else: # other replace_types
            #print(line['children'][0]['line_raw'])
            for tag in rtags:
                t = Mgff.features[Name2ID[tag]][0]
                tmp = {}
                tmp['line'] = t
                if len(t['parents']) == 0:
                    tmp['parent'] = t
                    tmp['num_isoforms'] = 1
                else:
                    tmp['parent'] = t['parents'][0][-1]
                    tmp['num_isoforms'] = len(t['parents'][0][-1]['children'])
                targets.append(tmp)
                mid.append(t['attributes']['ID'])
            if not line['attributes'].has_key('modified_track'):
                newid = self.replacer_add(line, RG, Mgff)
                newtarget = Mgff.features[newid['ID']][0]
                midline = ','.join(mid)
                newtarget['attributes']['modified_track'] = '{0:s}:{1:s}'.format(line['attributes']['replace_type'], midline)
                try:
                    self.info.append('{0:s}\t{1:s}\t{2:s}\t{3:s}'.format(originalID, newtarget['attributes']['ID'], newtarget['attributes']['replace'], newtarget['attributes']['modified_track']))
                    #print('{0:s}\t{1:s}\t{2:s}\t{3:s}'.format(originalID, newtarget['attributes']['ID'], newtarget['attributes']['replace'], newtarget['attributes']['modified_track']))
                except:
                    pass

            for t in targets:
                if t['num_isoforms'] == 1:
                    Mgff.remove(t['line'])
                else:
                    t['line']['line_status'] = 'removed'
        if u1_types is not None:
            children = []
            unique = set()
            if newtarget['type'] in u1_types:
                children.append(newtarget)
            else:
                for child in gff3.collect_descendants(newtarget):
                    if child['type'] in u1_types:
                        if child['line_raw'] not in unique:
                            children.append(child)
                            unique.add(child['line_raw'])
        else:
            children = newtarget['children']
        num = len(children)
        for child in children:
            if child['attributes'].has_key('status') and (child['attributes']['status'] == 'Delete' or child['attributes']['status'] == 'delete'):
                child['attributes']['replace_type'] = 'Delete'

                if num == 1:
                    Mgff.remove(child)
                else:
                    child['line_status'] = 'removed'

    def replacer_multi (self, line, RG, Mgff, u1_types=None, u2_types=None, gff3=None):
        Name2ID = RG.mapName2ID
        rtags = line['attributes']['replace']
        originalID = line['attributes']['ID']
        targets = []
        mid = []
        newtarget=line
        if line['attributes']['replace_type'] == 'multi-ref':
            if u1_types is None:
                children = line['children']
            else:
                children = []
                unique = set()
                if line['type'] in u1_types:
                    children.append(line)
                else:
                    for child in gff3.collect_descendants(line):
                        if child['type'] in u1_types:
                            if child['line_raw'] not in unique:
                                children.append(child)
                                unique.add(child['line_raw'])
                children = sorted(children, key=lambda k: k['line_index'])

            replace_parent = {}
            # replace parent in g2 file
            for ri in line['attributes']['replace']:
                feature = Mgff.features[Name2ID[ri]][0]
                if u2_types is None:
                    parents = feature['parents']
                    for p_line in parents:
                        for p in p_line:
                            replace_parent[p['attributes']['ID']] = 1
                else:
                    for p in Mgff.collect_roots(feature):
                        replace_parent[p['attributes']['ID']] = 1
                feature['line_status'] = 'removed'
                descendants = Mgff.collect_descendants(feature)
                for d in descendants:
                    d['line_status'] = 'removed'
            # the child features of the replace parent in g2 file
            for k in replace_parent:
                feature = Mgff.features[k][0]
                if u2_types is None:
                    childrenM = feature['children']
                else:
                    childrenM = []
                    if feature['type'] in u2_types:
                        childrenM.append(feature)
                    else:
                        for child in Mgff.collect_descendants(feature):
                            if child['type'] in u2_types:
                                childrenM.append(child)
                    childrenM = sorted(childrenM, key=lambda kid: kid['line_index'])
                # Currently, we will remove all orphan features and its parent
                for child in childrenM:
                    if 'Name' in child['attributes']:
                        if child['attributes']['Name'] not in line['attributes']['replace']:
                            line['attributes']['replace'].append(child['attributes']['Name'])
                    elif 'ID' in child['attributes']:
                        if child['attributes']['ID'] not in line['attributes']['replace']:
                            line['attributes']['replace'].append(child['attributes']['ID'])
                    child['line_status'] = 'removed'
                    child['attributes']['replace_type'] = 'multi-ref'
                    descendants = Mgff.collect_descendants(feature)
                    for d in descendants:
                        d['line_status'] = 'removed'
                feature['line_status'] = 'removed'

            cid = list()
            for child in children:
                cid.append('# \t- Transcripts: {0:s}'.format(child['attributes']['ID']))

            if not line['attributes'].has_key('modified_track'):
                newid = self.replacer_add(line, RG, Mgff)
                newtarget = Mgff.features[newid['ID']][0]
                newtarget['attributes']['modified_track'] = '{0:s}:{1:s}'.format(line['attributes']['replace_type'], originalID)
                self.info.append('{0:s}\t{1:s}\t{2:s}\t{3:s}'.format(originalID, newtarget['attributes']['ID'], newtarget['attributes']['replace'], newtarget['attributes']['modified_track']))
            tmp = ["No action"]
            return('# Add {0:s} as {1:s}, and remove {2:s}\n{3:s}\n#\t- Post-precessing of the models: {4:s}'.format(originalID,newid['ID'],str(line['attributes']['replace']), '\n'.join(cid), '\n'.join(tmp)))

        else:
            return('[Warning]\tCannot process {0:s}'.format(originalID))

