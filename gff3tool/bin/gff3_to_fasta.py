#! /usr/local/bin/python2.7
import sys
import re
import logging
import string
from gff3tool.lib.gff3 import Gff3
import gff3tool.lib.function4gff as function4gff
import gff3tool.lib.intra_model as intra_model
import gff3tool.lib.single_feature as single_feature
import gff3tool.lib.ERROR as ERROR
from gff3tool.bin import version


__version__ = version.__version__


COMPLEMENT_TRANS = string.maketrans('TAGCtagc', 'ATCGATCG')
def complement(seq):
    return seq.translate(COMPLEMENT_TRANS)

def get_subseq(gff, line, embedded_fasta=False):
    # it would give positive strand out as default, unless the strand information is given as '-'
    try:
        start = line['start']-1
    except:
        pass
    end = line['end']
    try:
        if gff.fasta_external and not embedded_fasta:
            string = gff.fasta_external[line['seqid']]['seq'][start:end]
        else:
            string = gff.fasta_embedded[line['seqid']]['seq'][start:end]
    except:
         if line['type'] != "CDS":
             print('WARNING  [SeqID/Start/End] Missing SeqID, or Start/End is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
         else:
             print('WARNING  [SeqID/Start/End/Phase] Missing SeqID, or Start/End/Phase is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
         string = ""
    #print(line['strand'], (line['start']-1), line['end'])
    #print('-->', line['strand'], start, end)
    if line['strand'] == '-':
        string = complement(string[::-1])
    return string

# Features of the translation funtion of this program,
# 1. translation from 64 combitions of codons
# 2. translation from codons with IUB Depiction
# 3. translation from mRNA (U contained) or CDS (T, instead of U contained)
BASES = ['T', 'C', 'A', 'G']
CODONS = [a+b+c for a in BASES for b in BASES for c in BASES]
CODONS.extend(['GCN', 'TGY', 'GAY', 'GAR', 'TTY', 'GGN', 'CAY', 'ATH', 'AAR', 'TTR', 'CTN', 'YTR', 'AAY', 'CCN', 'CAR', 'CGN', 'AGR', 'MGR', 'TCN', 'AGY', 'ACN', 'GTN', 'NNN', 'TAY', 'TAR', 'TRA']) # IUB Depiction
AMINO_ACIDS = 'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGGACDEFGHIKLLLNPQRRRSSTVXY**'
CODON_TABLE = dict(zip(CODONS, AMINO_ACIDS))
def translator(seq):
    seq = seq.upper().replace('\n', '').replace(' ', '').replace('U', 'T')
    peptide = ''
    for i in xrange(0, len(seq), 3):
        codon = seq[i: i+3]
        amino_acid = CODON_TABLE.get(codon, '!')
        if amino_acid != '!': # end of seq
            peptide += amino_acid
    return peptide

def splicer(gff, ftype, dline, stype, embedded_fasta=False):
    seq=dict()
    segments_Set = set()
    sort_seg = []
    roots = []
    u_parents = []
    for line in gff.lines:
        if stype == "user_defined":
            if line['type'] == ftype[0]:
                u_parents.append(line)
        try:
            if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                if len(line['attributes']) != 0:
                    roots.append(line)
                else:
                    print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
        except:
            print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
    #roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    if stype == "user_defined":
        if len(u_parents) == 0:
            print('WARNING   There is no {0:s} feature in the input gff. The sequence won\'t be generated.'.format(ftype[0]))
        for u_parent in u_parents:
            rid = 'NA'
            if u_parent['attributes'].has_key('Parent'):
                rid = ",".join(u_parent['attributes']['Parent'])
            cid = 'NA'
            if u_parent['attributes'].has_key('ID'):
                cid = u_parent['attributes']['ID']
            cname = cid
            if u_parent['attributes'].has_key('Name'):
                cname = u_parent['attributes']['Name']
            defline='>{0:s}'.format(cid)
            if dline == 'complete':
                try:
                    if rid != 'NA':
                        defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}({8:s})|Parent={5:s}|ID={6:s}|Name={7:s}'.format(u_parent['seqid'], u_parent['start'], u_parent['end'], u_parent['strand'], u_parent['type'], rid, cid, cname, ftype[0])
                    else:
                        defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{6:s}|ID={4:s}|Name={5:s}'.format(u_parent['seqid'], u_parent['start'], u_parent['end'], u_parent['strand'], cid, cname, u_parent['type'])
                except:
                    pass
            u_children = u_parent['children']
            segments = []
            segments_Set = set()
            for u_child in u_children:
                if u_child['type'] == ftype[1]:
                    segments.append(u_child)
                    segments_Set.add(u_child['line_index'])
                if u_child['type'] == "":
                    print('WARNING  [Missing feature type] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(u_child['line_index']+1), u_child['line_raw']))
            if len(segments) == 0:
                print('WARNING  There is no {0:s} feature for {1:s} in the input gff. The sequence of {1:s} is not generated.'.format(ftype[1],cid))
            sort_seg = function4gff.featureSort(segments)
            if u_child['strand'] == '-':
                sort_seg = function4gff.featureSort(segments, reverse=True)
            tmpseq = ''
            count = 0
            for s in sort_seg:
                segments_Set.discard(s['line_index'])
                if count == 0:
                    start, end = int, int
                    line = s
                    if line['type'] == 'CDS':
                        if not isinstance(line['phase'], int):
                            print('WARNING   No phase information!\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                        try:
                            start = line['start']+line['phase']
                        except:
                            if not isinstance(line['start'], int):
                                print('WARNING  [Start] Start is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                        end = line['end']
                        if line['strand'] == '-':
                            start = line['start']
                            try:
                                end = line['end']-line['phase']
                            except:
                                if not isinstance(line['end'], int):
                                    print('WARNING  [End] End is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                    else:
                        start = line['start']
                        end = line['end']
                    s['start'] = start
                    s['end'] = end
                    s['phase'] = 0
                tmpseq = tmpseq + get_subseq(gff, s, embedded_fasta)
                count += 1
            seq[defline] = tmpseq
            if len(segments_Set) != 0:
                for seg in segments_Set:
                    if len(sort_seg) != 0:
                        print('WARNING  [SeqID/Start/End/Phase] Missing SeqID, or Start/End/Phase is not a valid integer. User_defined output file might have incorrect sequence.\n\t\t- Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                    else:
                        try:
                            if gff.lines[seg]['seqid'] == "":
                                print('WARNING  [SeqID] Missing SeqID.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                            try:
                                int(gff.lines[seg]['start'])
                            except:
                                print('WARNING  [Start] Start is not a valid integer.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                            try:
                                int(gff.lines[seg]['end'])
                            except:
                                print('WARNING  [End] End is not a valid integer.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                        except:
                            print('WARNING  [SeqID] Missing SeqID.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))

    else:
        for root in roots:
            #if ftype[0] == 'CDS' and root['type'] == 'pseudogene': # pseudogene should not contain cds
                #continue
            rid = 'NA'
            if root['attributes'].has_key('ID'):
               rid = root['attributes']['ID']

            children = root['children']
            for child in children:
                cid = 'NA'
                if child['attributes'].has_key('ID'):
                    cid = child['attributes']['ID']
                cname = cid
                if child['attributes'].has_key('Name'):
                    cname = child['attributes']['Name']
                defline='>{0:s}'.format(cid)
                if stype == "pep":
                    cid = re.sub(r'(.+-)(R)([a-zA-Z]+)', r'\1P\3', cid)
                    defline = '>{0:s}'.format(cid)
                elif ftype[0] == 'CDS':
                    defline='>{0:s}-CDS'.format(cid)
                if dline == 'complete':
                    try:
                        if stype == 'pep':
                            cname = re.sub(r'(.+-)(R)([a-zA-Z]+)', r'\1P\3', cname)
                        defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}({8:s})|Parent={5:s}|ID={6:s}|Name={7:s}'.format(child['seqid'], child['start'], child['end'], child['strand'], child['type'], rid, cid, cname, ftype[0])
                    except:
                        pass
                segments = []
                segments_Set = set()
                gchildren = child['children']
                for gchild in gchildren:
                    if gchild['type'] in ftype:
                        segments.append(gchild)
                        segments_Set.add(gchild['line_index'])
                    if gchild['type'] == "":
                        print('WARNING  [Missing feature type] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(gchild['line_index']+1), gchild['line_raw']))

                flag = 0
                if len(segments)==0:
                    flag += 1
                    for gchild in gchildren:
                        if gchild['type'] == 'CDS':
                            segments.append(gchild)

                if len(segments)==0 and ftype[0] == 'CDS':
                    flag += 1
                    print("WARNING  There are no CDSs for {0:s} in the canonical gene model style. The sequence of {0:s} is not generated. If your gene models are non-canonical, use the argument -st user_defined, and specify the parent and child features with the -u argument.".format(cid))
                    continue
                elif len(segments)==0:
                    flag += 1
                    print("WARNING  There are no exons, nor CDSs for {0:s} in the canonical gene model style. The sequence of {0:s} is not generated. If your gene models are non-canonical, use the argument -st user_defined, and specify the parent and child features with the -u argument.".format(cid))
                    continue

                if flag == 1:
                    print("WARNING  There is no exons for {0:s} in the canonical gene model style. No spliced transcript output file generated. If your gene models are non-canonical, use the argument -st user_defined, and specify the parent and child features with the -u argument.".format(cid))
                    continue
                sort_seg = function4gff.featureSort(segments)
                if gchild['strand'] == '-':
                    sort_seg = function4gff.featureSort(segments, reverse=True)

                tmpseq = ''
                count = 0
                for s in sort_seg:
                    segments_Set.discard(s['line_index'])
                    if count == 0:
                        start, end = int, int
                        line = s
                        if line['type'] == 'CDS':
                            if not isinstance(line['phase'], int):
                                print('WARNING   No phase information!\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                                #sys.exit('[Error] No phase information!\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                            try:
                                start = line['start']+line['phase']
                            except:
                                if not isinstance(line['start'], int):
                                     print('WARNING  [Start] Start is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                            end = line['end']
                            if line['strand'] == '-':
                                start = line['start']
                                try:
                                    end = line['end']-line['phase']
                                except:
                                    if not isinstance(line['end'], int):
                                        print('WARNING  [End] End is not a valid integer.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
                        else:
                            start = line['start']
                            end = line['end']

                        s['start'] = start
                        s['end'] = end
                        s['phase'] = 0
                    tmpseq = tmpseq + get_subseq(gff, s, embedded_fasta)
                    count += 1

                seq[defline] = tmpseq
                if len(segments_Set) != 0:
                    for seg in segments_Set:
                        if len(sort_seg) != 0:
                            if gff.lines[seg]['type'] == 'exon' or gff.lines[seg]['type'] == 'pseudogenic_exon':
                                print('WARNING  [SeqID/Start/End] Missing SeqID, or Start/End is not a valid integer. Trans output file might have incorrect sequence.\n\t\t- Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                            elif gff.lines[seg]['type'] == 'CDS':
                                print('WARNING  [SeqID/Start/End/Phase] Missing SeqID, or Start/End/Phase is not a valid integer. CDS, pep output file might have incorrect sequence.\n\t\t- Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                        else:
                            try:
                                if gff.lines[seg]['seqid'] == "":
                                    print('WARNING  [SeqID] Missing SeqID.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                                try:
                                    int(gff.lines[seg]['start'])
                                except:
                                    print('WARNING  [Start] Start is not a valid integer.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                                try:
                                    int(gff.lines[seg]['end'])
                                except:
                                    print('WARNING  [End] End is not a valid integer.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))
                            except:
                                print('WARNING  [SeqID] Missing SeqID.\n\t\t-Line {0:s}: {1:s}'.format(str(gff.lines[seg]['line_index']+1), gff.lines[seg]['line_raw']))

    return seq

def extract_start_end(gff, stype, dline, embedded_fasta=False):
    '''Extract sequences for a feature only use the Start and End information. The relationship between parent and children would be ignored.'''
    seq=dict()
    roots = []
    for line in gff.lines:
        try:
            if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent'):
                if len(line['attributes']) != 0:
                    roots.append(line)
                else:
                    print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
        except:
            print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(line['line_index']+1), line['line_raw']))
    #roots = [line for line in gff.lines if line['line_type'] == 'feature' and not line['attributes'].has_key('Parent')]
    if stype == 'pre_trans':
        for root in roots:
            rid = 'NA'
            if root['attributes'].has_key('ID'):
                rid = root['attributes']['ID']
            children = root['children']
            for child in children:
                cid = 'NA'
                if child['attributes'].has_key('ID'):
                    cid = child['attributes']['ID']
                cname = cid
                if child['attributes'].has_key('Name'):
                    cname = child['attributes']['Name']
                defline='>{0:s}'.format(cid)
                if dline == 'complete':
                    try:
                        defline = '>{0:s}:{1:d}..{2:d}:{3:s}|genomic_sequence({4:s})|Parent={5:s}|ID={6:s}|Name={7:s}'.format(child['seqid'], child['start'], child['end'], child['strand'], child['type'], rid, cid, cname)
                    except:
                        pass
                seq[defline] = get_subseq(gff, child, embedded_fasta)
    elif stype == 'gene':
        for root in roots:
            if root['type'] == 'gene' or root['type'] == 'pseudogene':
                rid = 'NA'
                if root['attributes'].has_key('ID'):
                    rid = root['attributes']['ID']
                rname = rid
                if root['attributes'].has_key('Name'):
                    rname = root['attributes']['ID']
                defline='>{0:s}'.format(rid)
                if dline == 'complete':
                    defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{6:s}|ID={4:s}|Name={5:s}'.format(root['seqid'], root['start'], root['end'], root['strand'], rid, rname, root['type'])
                seq[defline] = get_subseq(gff, root, embedded_fasta)
            elif root['type'] == "":
                print('WARNING  [Missing feature type] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(root['line_index']+1), root['line_raw']))
    elif stype == 'exon':
        exons = [line for line in gff.lines if line['type'] == 'exon' or line['type'] == 'pseudogenic_exon']
        for exon in exons:
            try:
                eid = 'NA'
                if exon['attributes'].has_key('ID'):
                    eid = exon['attributes']['ID']
                ename = eid
                if exon['attributes'].has_key('Name'):
                    ename = exon['attributes']['Name']
                parents = exon['parents']
                plist = dict()
                for parent in parents:
                    for p in parent:
                        plist[p['attributes']['ID']] = 1

                keys = plist.keys()
                pid = ','.join(keys)

                defline='>{0:s}'.format(eid)
                if dline == 'complete':
                    defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}|Parent={5:s}|ID={6:s}|Name={7:s}'.format(exon['seqid'], exon['start'], exon['end'], exon['strand'], exon['type'], pid, eid, ename)

                seq[defline] = get_subseq(gff, exon, embedded_fasta)
            except:
                print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(exon['line_index']+1), exon['line_raw']))
    else:
        #user-defined pre_trans sequence
        user_defineds = [line for line in gff.lines if line['type'] == stype]
        for user_defined in user_defineds:
            try:
                uid = 'NA'
                if user_defined['attributes'].has_key('ID'):
                    uid = user_defined['attributes']['ID']
                uname = uid
                if user_defined['attributes'].has_key('Name'):
                    uname = user_defined['attributes']['Name']
                parents = user_defined['parents']
                plist = dict()
                for parent in parents:
                    for p in parent:
                        plist[p['attributes']['ID']] = 1
                keys = plist.keys()
                pid = ','.join(keys)
                defline='>{0:s}'.format(uid)
                if dline == 'complete':
                    if pid != "":
                        defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}|Parent={5:s}|ID={6:s}|Name={7:s}'.format(user_defined['seqid'], user_defined['start'], user_defined['end'], user_defined['strand'], user_defined['type'], pid, uid, uname)
                    else:
                        defline = '>{0:s}:{1:d}..{2:d}:{3:s}|{4:s}|ID={5:s}|Name={6:s}'.format(user_defined['seqid'], user_defined['start'], user_defined['end'], user_defined['strand'], user_defined['type'], uid, uname)
                    seq[defline] = get_subseq(gff, user_defined, embedded_fasta)
            except:
                print('WARNING  [Missing Attributes] Program failed.\n\t\t- Line {0:s}: {1:s}'.format(str(user_defined['line_index']+1), user_defined['line_raw']))

    return seq

def main(gff_file=None, fasta_file=None, embedded_fasta=False, stype=None, user_defined=None, dline=None, qc=True, output_prefix=None, logger=None):
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)

    if not gff_file or (not fasta_file and not embedded_fasta) or not stype:
        print('Gff file, fasta file, and type of extracted sequences need to be specified')
        sys.exit(1)
    type_set=['gene','exon','pre_trans', 'trans', 'cds', 'pep', 'all', 'user_defined']
    if not stype in type_set:
        logger.error('Your sequence type is "{0:s}". Sequence type must be one of {1:s}!'.format(stype, str(type_set)))
        sys.exit(1)

    if stype == 'all' and output_prefix:
        pass
    elif stype != 'all' and output_prefix:
        logger.info('Specifying prefix of output file name: (%s)...', output_prefix)
        fname = '{0:s}_{1:s}.fa'.format(output_prefix, stype)
        report_fh = open(fname, 'wb')
    else:
        print('[Error] Please specify the prefix of output file name...')
        sys.exit(1)
    if stype == 'user_defined' and user_defined != None:
        if len(user_defined) != 2:
            logger.error('Please specify parent and child feature via the -u argument. Format: [parent feature type],[child feature type]')
            sys.exit(1)
    elif stype != 'user_defined' and user_defined != None:
        logger.warning('Your sequence type is "{0:s}", -u argument will be ignored.'.format(stype))
    elif stype == 'user_defined' and user_defined == None:
        logger.error('-u is needed in combination with -st user_defined.')
        sys.exit(1)

    logger.info('Reading files: {0:s}, {1:s}...'.format(gff_file, fasta_file))
    gff=None

    if qc:
        initial_phase = False
        gff = Gff3(gff_file=gff_file, fasta_external=fasta_file, logger=logger)
        if embedded_fasta and len(gff.fasta_embedded) == 0:
            logger.error('There is no embedded fasta in the GFF3 file.')
            sys.exit(1)
        logger.info('Checking errors...')
        gff.check_parent_boundary()
        gff.check_phase(initial_phase)
        gff.check_reference()
        error_set = function4gff.extract_internal_detected_errors(gff)
        t = intra_model.main(gff, logger=logger)
        if t:
            error_set.extend(t)
        t = single_feature.main(gff, logger=logger)
        if t:
            error_set.extend(t)

        if error_set and len(error_set):
            escaped_error = ['Esf0012','Esf0033']
            eSet = list()
            for e in error_set:
                if not e['eCode'] in escaped_error:
                    eSet.append(e)
            if len(eSet):
                logger.warning('The extracted sequences might be wrong for the following features which have formatting errors...')
                print('ID\tError_Code\tError_Tag')
                for e in eSet:
                    tag = '[{0:s}]'.format(e['eTag'])
                    print e['ID'], e['eCode'], tag
    else:
        gff = Gff3(gff_file=gff_file, fasta_external=fasta_file, logger=logger_null)
        if embedded_fasta and len(gff.fasta_embedded) == 0:
            logger.error('There is no embedded fasta in the GFF3 file.')

    logger.info('Extract sequences for {0:s}...'.format(stype))
    seq=dict()
    if stype == 'all':
        if output_prefix:
            logger.info('Specifying prefix of output file name: (%s)...', output_prefix)
            pass
        else:
            print('[Error] Please specify the prefix of output file name...')
            sys.exit(1)

        tmp_stype = 'pre_trans'
        logger.info('\t- Extract sequences for {0:s}...'.format(tmp_stype))
        seq = extract_start_end(gff, tmp_stype, dline, embedded_fasta)
        if len(seq):
            fname = '{0:s}_{1:s}.fa'.format(output_prefix, tmp_stype)
            report_fh = open(fname, 'wb')
            logger.info('\t\tPrint out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, tmp_stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

        seq=dict()
        tmp_stype = 'gene'
        logger.info('\t- Extract sequences for {0:s}...'.format(tmp_stype))
        seq = extract_start_end(gff, tmp_stype, dline, embedded_fasta)
        if len(seq):
            fname = '{0:s}_{1:s}.fa'.format(output_prefix, tmp_stype)
            report_fh = open(fname, 'wb')
            logger.info('\t\tPrint out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, tmp_stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

        seq=dict()
        tmp_stype = 'exon'
        logger.info('\t- Extract sequences for {0:s}...'.format(tmp_stype))
        seq = extract_start_end(gff, tmp_stype, dline, embedded_fasta)
        if len(seq):
            fname = '{0:s}_{1:s}.fa'.format(output_prefix, tmp_stype)
            report_fh = open(fname, 'wb')
            logger.info('\t\tPrint out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, tmp_stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

        seq=dict()
        tmp_stype = 'trans'
        feature_type = ['exon', 'pseudogenic_exon']
        logger.info('\t- Extract sequences for {0:s}...'.format(tmp_stype))
        seq = splicer(gff, feature_type, dline, stype, embedded_fasta)
        if len(seq):
            fname = '{0:s}_{1:s}.fa'.format(output_prefix, tmp_stype)
            report_fh = open(fname, 'wb')
            logger.info('\t\tPrint out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, tmp_stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

        seq=dict()
        tmp_stype = 'cds'
        feature_type = ['CDS']
        logger.info('\t- Extract sequences for {0:s}...'.format(tmp_stype))
        seq = splicer(gff, feature_type, dline, stype, embedded_fasta)
        if len(seq):
            fname = '{0:s}_{1:s}.fa'.format(output_prefix, tmp_stype)
            report_fh = open(fname, 'wb')
            logger.info('\t\tPrint out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, tmp_stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

        seq=dict()
        tmp_stype = 'pep'
        feature_type = ['CDS']
        logger.info('\t- Extract sequences for {0:s}...'.format(tmp_stype))
        tmpseq = splicer(gff, feature_type, dline, tmp_stype, embedded_fasta)
        for k,v in tmpseq.items():
            k = k.replace("|mRNA(CDS)|", "|peptide|")
            v = translator(v)
            seq[k] = v
        if len(seq):
            fname = '{0:s}_{1:s}.fa'.format(output_prefix, tmp_stype)
            report_fh = open(fname, 'wb')
            logger.info('\t\tPrint out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, tmp_stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))
    elif stype == 'user_defined':
        feature_type = [user_defined[0],user_defined[1]]
        seq = splicer(gff, feature_type,  dline, stype, embedded_fasta)
        if len(seq):
            logger.info('Print out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

    else:
        if stype == 'pre_trans' or stype == 'gene' or stype == 'exon':
            seq = extract_start_end(gff, stype, dline, embedded_fasta)
        elif stype == 'trans':
            feature_type = ['exon', 'pseudogenic_exon']
            seq = splicer(gff, feature_type,  dline, stype, embedded_fasta)
        elif stype == 'cds':
            feature_type = ['CDS']
            seq = splicer(gff, feature_type,  dline, stype, embedded_fasta)
        elif stype == 'pep':
            feature_type = ['CDS']
            tmpseq = splicer(gff, feature_type,  dline, stype, embedded_fasta)
            for k,v in tmpseq.items():
                k = k.replace("|mRNA(CDS)|", "|peptide|")
                #k = re.sub(r'(.*-)(R)(.)',r'\1P\3',k)
                v = translator(v)
                seq[k] = v
        if len(seq):
            logger.info('Print out extracted sequences: {0:s}_{1:s}.fa...'.format(output_prefix, stype))
            for k,v in seq.items():
                if len(k)!=0 and len(v)!=0:
                    report_fh.write('{0:s}\n{1:s}\n'.format(k,v))

def script_main():
    logger_stderr = logging.getLogger(__name__+'stderr')
    logger_stderr.setLevel(logging.INFO)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logger_stderr.addHandler(stderr_handler)

    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)
    import argparse
    from textwrap import dedent
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=dedent("""\
    Extract sequences from specific regions of genome based on gff file.
    Testing enviroment:
    1. Python 2.7

    Required inputs:
    1. GFF3: specify the file name with the -g argument
    2. Fasta file: specify the file name with the -f argument
    3. Output prefix: specify with the -o argument

    Outputs:
    1. Fasta formatted sequence file based on the gff3 file.

    Example command:
    gff3_to_fasta -g example_file/example.gff3 -f example_file/reference.fa -st all -d simple -o test_sequences

    """))
    parser.add_argument('-g', '--gff', type=str, help='Genome annotation file in GFF3 format')
    parser.add_argument('-f', '--fasta', type=str, help='Genome sequences in FASTA format')
    parser.add_argument('-embf', '--embedded_fasta', action='store_true', help='Specify this option if you want to extract sequence from embedded fasta.', default=False)
    parser.add_argument('-st', '--sequence_type', type=str, help="{0:s}\n\t{1:s}\n\t{2:s}\n\t{3:s}\n\t{4:s}\n\t{5:s}\n\t{6:s}\n\t{7:s}\n\t{8:s}".format('Type of sequences you would like to extract: ','"all" - FASTA files for all types of sequences listed below, except user_defined;','"gene" - gene sequence for each record;', '"exon" - exon sequence for each record;', '"pre_trans" - genomic region of a transcript model (premature transcript);', '"trans" - spliced transcripts (only exons included);', '"cds" - coding sequences;', '"pep" - peptide sequences;', '"user_defined" - specify parent and child features via the -u argument.'))
    parser.add_argument('-u', '--user_defined', nargs='*', help="Specify parent and child features for fasta extraction, format: [parent feature type] [child feature type] (ex: -u mRNA CDS). Required if -st user_defined is given.")
    parser.add_argument('-d', '--defline', type=str, help="{0:s}\n\t{1:s}\n\t{2:s}".format('Defline format in the output FASTA file:','"simple" - only ID would be shown in the defline;', '"complete" - complete information of the feature would be shown in the defline.'))
    parser.add_argument('-o', '--output_prefix', type=str, help='Prefix of output file name')
    parser.add_argument('-noQC', '--quality_control', action='store_false', help='Specify this option if you do not want to execute quality control for gff file. (default: QC is executed)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()
    if args.gff:
        logger_stderr.info('Checking gff file (%s)...', args.gff)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        logger_stderr.error('Required field -g missing...')
        sys.exit(1)

    if args.fasta:
        logger_stderr.info('Checking genome fasta (%s)...', args.fasta)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.fasta = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        if not args.embedded_fasta:
            parser.print_help()
            logger_stderr.error('Required field -f missing...')
            sys.exit(1)

    if args.sequence_type:
        logger_stderr.info('Specifying sequence type: (%s)...', args.sequence_type)
        if args.sequence_type == "user_defined":
            if not args.user_defined:
                parser.print_help()
                logger_stderr.error('-u is needed in combination with -st user_defined. format: [parent feature type] [child feature type] (ex: -u mRNA CDS)')
                sys.exit(1)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.sequence_type = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        logger_stderr.error('Required field -st missing...')
        sys.exit(1)

    if args.defline:
        logger_stderr.info('Defline format: (%s)...', args.defline)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.defline = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        logger_stderr.error('Required field -d missing...')
        sys.exit(1)


    main(args.gff, args.fasta, args.embedded_fasta, args.sequence_type, args.user_defined, args.defline, args.quality_control, args.output_prefix, logger_stderr)
