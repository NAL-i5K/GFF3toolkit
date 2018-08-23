#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import defaultdict
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
import re
import string
import copy
import logging
logger = logging.getLogger(__name__)
#log.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
logger.setLevel(logging.INFO)
if not logger.handlers:
    lh = logging.StreamHandler()
    lh.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger.addHandler(lh)

def idgenerator(prefix, lastnumber, digitlen):
    lastnumber += 1
    idnum = str(lastnumber)
    if len(idnum) < digitlen:
        adddigit = digitlen-len(idnum)
        for _ in range(adddigit):
            idnum = str(0) + idnum
    result={}
    result['ID'] = prefix + idnum
    result['maxnum'] = lastnumber
    return(result)

def simpleIDreplace(model, newid):
    tmp  = re.search('(.+?)(\d+)',newid)
    newidnumber = tmp.groups()[1]
    if model['attributes'].has_key('ID'):
        tmp  = re.search('(.+?)(\d+)(.*)',model['attributes']['ID'])
        prefix, _, suffix = tmp.groups()[0], tmp.groups()[1], tmp.groups()[2]
        renamedID = prefix + newidnumber + suffix
        model['attributes']['ID'] = renamedID
    else:
        renamedID = newid + model['type']
        model['attributes']['ID'] = renamedID

def newParentModel(oldmodel, newid, gff):
    newmodel = copy.deepcopy(oldmodel)
    if oldmodel['attributes'].has_key('Name') and oldmodel['attributes']['Name'] == oldmodel['attributes']['ID']:
        newmodel['attributes']['Name'] = newid
    elif not oldmodel['attributes'].has_key('Name'):
        newmodel['attributes']['Name'] = newid
    newmodel['attributes']['ID'] = newid
    eofindex = len(gff.lines)
    newmodel['line_index'] = eofindex
    newmodel['children'] = []
    return newmodel

def newChildModel(ochild, newid, gff):
    nchild = copy.deepcopy(ochild)
    eofindex = len(gff.lines)
    nchild['line_index'] = eofindex
    nchild['parents'] = []
    nchild['attributes']['Parent']=[]
    if newid:
        simpleIDreplace(nchild, newid)
    if ochild['attributes'].has_key('Name') and ochild['attributes']['Name'] == ochild['attributes']['ID']:
        nchild['attributes']['Name'] = nchild['attributes']['ID']
    if nchild.has_key('children'):
        nchild['children'] = []
    return nchild

def newPepModel(ochild, gff):
    # ochild must be a mRNA feature
    gchildren = ochild['children']
    start, end = int(), int()
    newpep = {}
    flag = 0
    for gchild in gchildren:
        if gchild['type'] == 'CDS':
            if flag == 0:
                newpep = copy.deepcopy(gchild)
                start, end = gchild['start'], gchild['end']
            if gchild['start'] < start:
                start = gchild['start']
            if gchild['end'] > end:
                end = gchild['end']
            flag+=1
    if flag > 0:
        eofindex = len(gff.lines)
        newpep['line_index'] = eofindex
        newpep['start'] = start
        newpep['end'] = end
        newpep['type'] = 'polypeptide'
        tmp = re.search('-R(.)-CDS$', newpep['attributes']['ID'])
        newpep['attributes']['ID'] = re.sub('-R.*', '-P{0:s}'.format(tmp.groups()[0]), newpep['attributes']['ID'])
        if newpep['attributes'].has_key('Name') and newpep['attributes']['Name'] == newpep['attributes']['Name']:
            newpep['attributes']['Name'] = newpep['attributes']['ID']
        if newpep.has_key('children'):
            newpep['children'] = []
        ochild['children'].append(newpep)
        gff.features[newpep['attributes']['ID']].append(newpep)
        gff.lines.append(newpep)

def threadin(oldmodel, newid, gff): #implement later 09/01/2015
    pass

def newModel(oldmodel, newid, gff):
    '''
	 model should be root model.
	 '''
    newmodel = newParentModel(oldmodel, newid, gff)
    gff.features[newid].append(newmodel)
    gff.lines.append(newmodel)

    oldchildren = oldmodel['children']
    maxindex = -1
    childids = {}
    otherlines = []
    for ochild in oldchildren:
        nchild = newChildModel(ochild, newmodel['attributes']['ID'], gff)
        nchild['parents'].append(gff.features[newmodel['attributes']['ID']])
        nchild['attributes']['Parent'].append(newmodel['attributes']['ID'])
        # generate new mRNA ID when merging multiple isoforms
        name_add_flag = 0
        if childids.has_key(nchild['attributes']['ID']):
            newalphabet = string.uppercase[(maxindex+1)]
            nchild['attributes']['ID'] = re.sub('(.)$',newalphabet,nchild['attributes']['ID'])
            name_add_flag += 1
        else:
            t = re.search('(.)$', nchild['attributes']['ID'])
            newindex = string.uppercase.index(t.groups()[0])
            if newindex > maxindex:
                maxindex = newindex
            childids[nchild['attributes']['ID']] = 0
        gff.features[nchild['attributes']['ID']].append(nchild)
        gff.lines.append(nchild)
        newmodel['children'].append(nchild)
        print('{0:s}\t{1:s}\t{2:s}'.format(nchild['attributes']['ID'], 'changed from', ochild['attributes']['ID']))

        oldgrandchildren = ochild['children']
        old2new = {}
        for ogchild in oldgrandchildren:
            ngchild = newChildModel(ogchild, nchild['attributes']['ID'], gff)
            # make child exons and CDSs to have IDs cositent with their parent
            if name_add_flag > 0 and not re.search(nchild['attributes']['ID'], ngchild['attributes']['ID']):
                tmp = re.search('(\w+)(\d+)-R(.)(.*)', ngchild['attributes']['ID'])
                idchange = nchild['attributes']['ID'] + tmp.groups()[3]
                ngchild['attributes']['ID'] = idchange
            ngchild['parents'].append(gff.features[nchild['attributes']['ID']])
            ngchild['attributes']['Parent'].append(nchild['attributes']['ID'])
            if ngchild['attributes'].has_key('ID'):
                gff.features[ngchild['attributes']['ID']].append(ngchild)
            gff.lines.append(ngchild)
            nchild['children'].append(ngchild)
            otherlines.extend(gff.collect_descendants(ogchild))
            if ngchild['attributes'].has_key('ID') and ogchild['attributes'].has_key('ID'):
                old2new[ogchild['attributes']['ID']] = ngchild['attributes']['ID']
                #print('{0:s}\t{1:s}\t{2:s}'.format(ngchild['attributes']['ID'], 'changed from', ogchild['attributes']['ID']))

        uniquek = {}
        for k in otherlines:
            uniquek[k['attributes']['ID']] = k
        for v, k in uniquek.items():
            parent_lines = k['parents']
            newk = newChildModel(k, nchild['attributes']['ID'], gff)
            uniqueparent = {}
            for parents in parent_lines:
					 for parent in parents:
						  newkpid = old2new[parent['attributes']['ID']]
						  uniqueparent[newkpid]=1
            if len(uniqueparent) == 1:
                for upi in uniqueparent:
                    newk['parents'].append(gff.features[upi])
                    newk['attributes']['Parent'].append(upi)
                if newk['attributes'].has_key('ID'):
                    newk['attributes']['ID'] = newk['attributes']['Parent'][0] + '-' + newk['type']
                    newk['attributes']['Name'] = newk['attributes']['ID']
                    gff.features[newk['attributes']['ID']].append(newk)
            else:
					 print('Warning!! features have multiple errors:\t' + k['attributes']['ID'])
            gff.lines.append(newk)
            parent_lines = newk['parents']
            for parents in parent_lines:
                for parent in parents:
                    parent['children'].append(newk)

    oldid = oldmodel['attributes']['ID']
    if re.search('\.s', oldid):
        return

def general_newModel(oldmodel, gff):
    '''
	 model should be root model.
    '''
    newid = oldmodel['attributes']['ID']
    if newid in gff.features.keys():
        eofindex = len(gff.lines)
        newid = eofindex
    newmodel = newParentModel(oldmodel, newid, gff)
    gff.features[newid].append(newmodel)
    gff.lines.append(newmodel)

    oldchildren = oldmodel['children']
    maxindex = -1
    childids = {}
    otherlines = []
    for ochild in oldchildren:
        nchild = newChildModel(ochild, None, gff)
        nchild['parents'].append(gff.features[newmodel['attributes']['ID']])
        nchild['attributes']['Parent'].append(newmodel['attributes']['ID'])
        # generate new mRNA ID when merging multiple isoforms
        name_add_flag = 0
        if childids.has_key(nchild['attributes']['ID']):
            #newalphabet = string.uppercase[(maxindex+1)]
            #nchild['attributes']['ID'] = re.sub('(.)$',newalphabet,nchild['attributes']['ID'])
            name_add_flag += 1
        else:
            #t = re.search('(.)$', nchild['attributes']['ID'])
            #newindex = string.uppercase.index(t.groups()[0])
            #if newindex > maxindex:
                #maxindex = newindex
            childids[nchild['attributes']['ID']] = 0

        gff.features[nchild['attributes']['ID']].append(nchild)
        gff.lines.append(nchild)
        newmodel['children'].append(nchild)
        #print('{0:s}\t{1:s}\t{2:s}'.format(nchild['attributes']['ID'], 'changed from', ochild['attributes']['ID']))

        oldgrandchildren = ochild['children']
        old2new = {}
        for ogchild in oldgrandchildren:
            ngchild = newChildModel(ogchild, None, gff)
            #print("!!!!!! {0:s}\t{1:s}".format(ogchild['attributes']['ID'],ngchild['attributes']['ID']))
            # make child exons and CDSs to have IDs cositent with their parent
            #if name_add_flag > 0 and not re.search(nchild['attributes']['ID'], ngchild['attributes']['ID']):
                #tmp = re.search('(\w+)(\d+)-R(.)(.*)', ngchild['attributes']['ID'])
                #idchange = nchild['attributes']['ID'] + tmp.groups()[3]
                #ngchild['attributes']['ID'] = idchange
            ngchild['parents'].append(gff.features[nchild['attributes']['ID']])
            ngchild['attributes']['Parent'].append(nchild['attributes']['ID'])
            if ngchild['attributes'].has_key('ID'):
                gff.features[ngchild['attributes']['ID']].append(ngchild)
            gff.lines.append(ngchild)
            nchild['children'].append(ngchild)
            otherlines.extend(gff.collect_descendants(ogchild))
            if ngchild['attributes'].has_key('ID') and ogchild['attributes'].has_key('ID'):
                old2new[ogchild['attributes']['ID']] = ngchild['attributes']['ID']
                #print('!!!!! {0:s}\t{1:s}\t{2:s}'.format(ngchild['attributes']['ID'], 'changed from', ogchild['attributes']['ID']))
            #print("!!!!!!After {0:s}\t{1:s}".format(ogchild['attributes']['ID'],ngchild['attributes']['ID']))


        uniquek = {}
        for k in otherlines:
            uniquek[k['attributes']['ID']] = k
        for v, k in uniquek.items():
            parent_lines = k['parents']
            newk = newChildModel(k, None, gff)

            uniqueparent = {}
            for parents in parent_lines:
                for parent in parents:
		    newkpid = old2new[parent['attributes']['ID']]
		    uniqueparent[newkpid]=1
            if len(uniqueparent) == 1:
                for upi in uniqueparent:
                    newk['parents'].append(gff.features[upi])
                    newk['attributes']['Parent'].append(upi)
                if newk['attributes'].has_key('ID'):
                    #newk['attributes']['ID'] = newk['attributes']['Parent'][0] + '-' + newk['type']
                    #newk['attributes']['Name'] = newk['attributes']['ID']
                    gff.features[newk['attributes']['ID']].append(newk)
            else:
					 print('Warning!! features have multiple errors:\t' + k['attributes']['ID'])

            gff.lines.append(newk)
            parent_lines = newk['parents']
            for parents in parent_lines:
                for parent in parents:
                    parent['children'].append(newk)

    oldid = oldmodel['attributes']['ID']
    if re.search('\.s', oldid):
        return



def newNreplaceModel(oldmodel, newid, gff):
    '''
	 model should be root model.
	 '''
    newmodel = newParentModel(oldmodel, newid, gff)
    gff.features[newid].append(newmodel)
    gff.lines.append(newmodel)

    oldchildren = oldmodel['children']
    maxindex = -1
    childids = {}
    for ochild in oldchildren:
        nchild = newChildModel(ochild, newmodel['attributes']['ID'], gff)
        nchild['parents'].append(gff.features[newmodel['attributes']['ID']])
        nchild['attributes']['Parent'].append(newmodel['attributes']['ID'])
        # generate new mRNA ID when merging multiple isoforms
        name_add_flag = 0
        if childids.has_key(nchild['attributes']['ID']):
            newalphabet = string.uppercase[(maxindex+1)]
            nchild['attributes']['ID'] = re.sub('(.)$',newalphabet,nchild['attributes']['ID'])
            name_add_flag += 1
        else:
            print('id_processor.py: {0:s}'.format(nchild['attributes']['ID']))
            t = re.search('(.)$', nchild['attributes']['ID'])
            newindex = string.uppercase.index(t.groups()[0])
            if newindex > maxindex:
                maxindex = newindex
            childids[nchild['attributes']['ID']] = 0
        gff.features[nchild['attributes']['ID']].append(nchild)
        gff.lines.append(nchild)
        newmodel['children'].append(nchild)
        print('{0:s}\t{1:s}\t{2:s}'.format(nchild['attributes']['ID'], 'changed from', ochild['attributes']['ID']))

        oldgrandchildren = ochild['children']
        for ogchild in oldgrandchildren:
            ngchild = newChildModel(ogchild, nchild['attributes']['ID'], gff)
            # make child exons and CDSs to have IDs cositent with their parent
            if name_add_flag > 0 and not re.search(nchild['attributes']['ID'], ngchild['attributes']['ID']):
                tmp = re.search('(\w+)(\d+)-R(.)(.*)', ngchild['attributes']['ID'])
                idchange = nchild['attributes']['ID'] + tmp.groups()[3]
                ngchild['attributes']['ID'] = idchange
            ngchild['parents'].append(gff.features[nchild['attributes']['ID']])
            ngchild['attributes']['Parent'].append(nchild['attributes']['ID'])
            if ngchild['attributes'].has_key('ID'):
                gff.features[ngchild['attributes']['ID']].append(ngchild)
            gff.lines.append(ngchild)
            nchild['children'].append(ngchild)
            if ngchild['attributes'].has_key('ID') and ogchild['attributes'].has_key('ID'):
                print('{0:s}\t{1:s}\t{2:s}'.format(ngchild['attributes']['ID'], 'changed from', ogchild['attributes']['ID']))
            #elif ngchild['attributes'].has_key('ID'):
                #print('{0:s}\t{1:s}\t{2:s}'.format(ngchild['attributes']['ID'], 'added to CDS of', nchild['attributes']['ID']))

    oldid = oldmodel['attributes']['ID']
    gff.remove(oldmodel)
    if re.search('\.s', oldid):
        return
    print('{0:s}\t{1:s}\t{2:s}'.format('', 'removed', oldid))


def IDprocessing(gff):
    roots = [line for line in gff.lines if line['line_type']=='feature' and not line['attributes'].has_key('Parent')]
    tmp  = re.search('(.+?)(\d+)',roots[0]['attributes']['ID'])
    idprefix = tmp.groups()[0]
    maxIDnumber = 0
    digitlen = 0
    for root in roots:
        rootid = root['attributes']['ID']
        if re.search(idprefix, rootid):
            tmp = re.search('(.+?)(\d+)',rootid)
            IDnumber = tmp.groups()[1]
            digitlen = len(IDnumber)
            if int(IDnumber) > maxIDnumber:
                maxIDnumber = int(IDnumber)
        children = root['children']
        for child in children:
            gchildren = child['children']
            for gchild in gchildren:
                if gchild['type'] == 'CDS' and not gchild['attributes'].has_key('ID'):
                    for pid in gchild['attributes']['Parent']:
                        gid = pid + '-CDS'
                        gchild['attributes']['ID'] = gid

    models = [line for line in gff.lines if line['line_type']=='feature' and line['attributes'].has_key('modified_track')]
    for model in models:
        track, modelid = model['attributes']['modified_track'], model['attributes']['ID']
        del model['attributes']['modified_track']
        if track == 'removed':
            print('{0:s}\t{1:s}\t{2:s}'.format('', 'removed', modelid))
            gff.remove(model)
        else:
            if re.search('_', track):
                tokens = track.split('_')
                for i in range(len(tokens)):
                    if re.search('\.s', tokens[i]):
                        tmp = re.search('(.+?)\.(s\d+)$', tokens[i])
                        tokens[i] = tmp.groups()[0]+'('+tmp.groups()[1]+')'
                line = ', '.join(tokens)
                newID = idgenerator(idprefix, maxIDnumber, digitlen)
                maxIDnumber = newID['maxnum']
                newNreplaceModel(model, newID['ID'], gff)
                print('{0:s}\t{1:s}\t{2:s}'.format(newID['ID'], 'merged from', line))
            elif re.search('\.s', track):
                children = model['children']
                childlist = []
                for child in children:
                    childlist.append(child['attributes']['ID'])
                childids = ', '.join(childlist)
                tmp = re.search('(.+?)\.(s\d+)$', track)
                track = tmp.groups()[0]+'('+tmp.groups()[1]+':'+childids+')'
                newID = idgenerator(idprefix, maxIDnumber, digitlen)
                maxIDnumber = newID['maxnum']
                newNreplaceModel(model, newID['ID'], gff)
                print('{0:s}\t{1:s}\t{2:s}'.format(newID['ID'], 'split from', track))

def ncbiNamingSystem(gff, tag):
    '''
    NCBI naming system
    1. add an attribute of 'locus_tag' (locus_tag=A271_CLEC000001) with a prefix of species submission code
    2. add attributes of 'transcript_id' (transcript_id=CLEC000002-RA) and 'protein_id' (protein_id=CLEC000002-PA) at both mRNA and CDS levels
    3. add an attribute of 'product' (product=really important protein) at CDS level if it exists

    locus_tag is added to top-level features including (Let Terence know about this),
        gene
        pseudogene
        substitution
    Additional attributes to some child features
        mRNA: 'transcript_id=' and 'protein_id=' are added
        other child features (such as pseudogenic_transcript, rRNA and so on): 'transcript_id=' is added
        CDS: 'transcript_id=', 'protein_id=' and 'product=' are added
    '''
    roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    roottype={}
    childtype={}
    grandchildtype={}
    for root in roots:
        roottype[root['type']]=0
        rid = root['attributes']['ID']
        locus_tag = tag + '_' + rid
        root['attributes']['locus_tag'] = locus_tag

        children = root['children']
        for child in children:
            cid, ctype = child['attributes']['ID'], child['type']
            childtype[ctype] = 0
            product='NA'
            if child['attributes'].has_key('Name') and not child['attributes']['Name'] == cid:
                product = child['attributes']['Name']

            transcript_id = cid
            protein_id = re.sub('-R', '-P', cid)
            if ctype == 'mRNA':
                child['attributes']['transcript_id'] = transcript_id
                child['attributes']['protein_id'] = protein_id
            else:
                child['attributes']['transcript_id'] = transcript_id

            gchildren = child['children']
            for gchild in gchildren:
                gctype = gchild['type']
                grandchildtype[gctype]=0
                if gctype == 'CDS':
                    gchild['attributes']['transcript_id'] = transcript_id
                    gchild['attributes']['protein_id'] = protein_id
                    if not product == 'NA':
                        gchild['attributes']['product'] = product
    print('## Types in this gff')
    for k in roottype:
        print('root type: ', k)
    for k in childtype:
        print('child types: ', k)
    for k in grandchildtype:
        print('grandchild types: ', k)

