#! /usr/local/bin/python2.7
# Contributed by Mei-Ju Chen <arbula [at] gmail [dot] com> (2015)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import sys
import re
import logging
import subprocess
import os
try:
    from subprocess import DEVNULL # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')
# try to import from project first
lib_path = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
from gff3tool.lib.gff3 import Gff3
import gff3tool.bin.gff3_to_fasta as gff3_to_fasta
import shutil

from gff3tool.bin import version

__version__ = version.__version__


def main(gff1, gff2, fasta, outdir, scode, logger, all_assign=False, user_defined1=None, user_defined2=None):
    logger_null = logging.getLogger(__name__+'null')
    null_handler = logging.NullHandler()
    logger_null.addHandler(null_handler)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    tmpdir = '{0:s}/{1:s}'.format(outdir, 'tmp')
    if not os.path.isdir(tmpdir):
        os.makedirs(tmpdir)

    #Check if there is a non-coding transcript
    transcripts = set()
    transcripts_type = set()
    gff3_1 = Gff3(gff_file=gff1, fasta_external=fasta, logger=logger)
    gff3_2 = Gff3(gff_file=gff2, fasta_external=fasta, logger=logger)

    makeblastdb_path = os.path.join(lib_path, 'ncbi-blast+', 'bin', 'makeblastdb')
    blastn_path = os.path.join(lib_path, 'ncbi-blast+', 'bin', 'blastn')

    if user_defined1 == None:
        roots =[]
        for line in gff3_1.lines:
            try:
                if line['line_type'] == 'feature':
                    # remove all the replace attributes
                    if all_assign and 'replace' in line['attributes']:
                        del line['attributes']['replace']
                    if 'Parent' not in line['attributes'] and len(line['attributes']) != 0:
                        roots.append(line)
            except:
                pass
        for root in roots:
            children = root['children']
            for child in children:
                cid = 'NA'
                if child['attributes'].has_key('ID'):
                    cid = child['attributes']['ID']
                defline = cid
                gchildren = child['children']
                CDSflag = 0
                for gchild in gchildren:
                    if gchild['type'] == 'CDS':
                        CDSflag += 1
                if CDSflag == 0:
                    transcripts.add(defline)
                if child.has_key('type'):
                    transcripts_type.add(child['type'])
    else:
        for lines in user_defined1:
            transcripts_type.add(lines[0])
        for line in gff3_1.lines:
            if line['line_type'] == 'feature':
                if all_assign and 'replace' in line['attributes']:
                    del line['attributes']['replace']
            if line['type'] in transcripts_type:
                id = str()
                if line['attributes'].has_key('ID'):
                    id = line['attributes']['ID']
                    transcripts.add(id)
    if all_assign:
        # modified gff1 without any relace attributes
        gff3_1_mod = os.path.join(tmpdir, 'gff1_mod.gff3')
        gff3_1.write(gff3_1_mod)
        gff1 = gff3_1_mod

    out1_type = os.path.join(tmpdir, 'gff1_transcript_type.txt')
    with open(out1_type, "w") as trans_type:
        for line in transcripts_type:
            trans_type.write(line+"\n")

    cmd = os.path.join(lib_path, 'auto_assignment', 'create_annotation_summaries_nov21-7.pl')
    logger.info('Generate info table for {0:s} by using {1:s}'.format(gff1, cmd))
    summary = os.path.join(tmpdir, 'summary_report.txt')
    subprocess.Popen(['perl', cmd, gff1, fasta, summary, scode, out1_type], stdout=DEVNULL).wait()

    logger.info('Extract sequences from {0:s}...'.format(gff1))
    out1 = os.path.join(tmpdir, 'gff1')
    if user_defined1 == None:
        logger.info('\tExtract CDS sequences...')
        gff3_to_fasta.main(gff_file=gff1, fasta_file=fasta, stype='cds', dline='complete', qc=False, output_prefix=out1, logger=logger_null)
        logger.info('\tExtract premature transcript sequences...')
        gff3_to_fasta.main(gff_file=gff1, fasta_file=fasta, stype='pre_trans', dline='complete', qc=False, output_prefix=out1, logger=logger_null)
        if len(transcripts) > 0:
            logger.info('\tExtract transcript sequences...')
            gff3_to_fasta.main(gff_file=gff1, fasta_file=fasta, stype='trans', dline='complete', qc=False, output_prefix=out1, logger=logger_null)
    else:
        logger.info('\tExtract user_defined_file1 sequences...')
        user_defined_out1 = '{0:s}_{1:s}'.format(out1, 'cds.fa')
        user_defined_pretrans1 = '{0:s}_{1:s}'.format(out1, 'pre_trans.fa')
        user_defined_tmp = '{0:s}_{1:s}'.format(out1, 'user_defined.fa')
        parent_type = set()
        with open(user_defined_out1, "w") as outfile:
            for lines in user_defined1:
                gff3_to_fasta.main(gff_file=gff1, fasta_file=fasta, stype='user_defined', user_defined=lines, dline='complete', qc=False, output_prefix=out1, logger=logger_null)
                with open(user_defined_tmp, 'rb') as fd:
                    shutil.copyfileobj(fd, outfile)
                parent_type.add(lines[0])

        with open(user_defined_pretrans1, "w") as outfile:
            for line in parent_type:
                seq = gff3_to_fasta.extract_start_end(gff3_1, line, 'complete')
                for k,v in seq.items():
                    if len(k)!=0 and len(v)!=0:
                        outfile.write('{0:s}\n{1:s}\n'.format(k,v))



    logger.info('Extract sequences from {0:s}...'.format(gff2))
    out2 = os.path.join(tmpdir, 'gff2')
    if user_defined2 == None:
        logger.info('\tExtract CDS sequences...')
        gff3_to_fasta.main(gff_file=gff2, fasta_file=fasta, stype='cds', dline='complete', qc=False, output_prefix=out2, logger=logger_null)
        logger.info('\tExtract premature transcript sequences...')
        gff3_to_fasta.main(gff_file=gff2, fasta_file=fasta, stype='pre_trans', dline='complete', qc=False, output_prefix=out2, logger=logger_null)
        if len(transcripts) > 0:
            logger.info('\tExtract transcript sequences...')
            gff3_to_fasta.main(gff_file=gff2, fasta_file=fasta, stype='trans', dline='complete', qc=False, output_prefix=out2, logger=logger_null)
    else:
        logger.info('\tExtract user_defined_file2 sequences...')
        user_defined_out2 = '{0:s}_{1:s}'.format(out2, 'cds.fa')
        user_defined_pretrans2 = '{0:s}_{1:s}'.format(out2, 'pre_trans.fa')
        user_defined_tmp = '{0:s}_{1:s}'.format(out2, 'user_defined.fa')
        parent_type = set()
        with open(user_defined_out2, "w") as outfile:
            for lines in user_defined2:
                gff3_to_fasta.main(gff_file=gff2, fasta_file=fasta, stype='user_defined', user_defined=lines, dline='complete', qc=False, output_prefix=out2, logger=logger_null)
                with open(user_defined_tmp, 'rb') as fd:
                    shutil.copyfileobj(fd, outfile)
                parent_type.add(lines[0])

        with open(user_defined_pretrans2, "w") as outfile:
            for line in parent_type:
                seq = gff3_to_fasta.extract_start_end(gff3_2, line, 'complete')
                for k,v in seq.items():
                    if len(k)!=0 and len(v)!=0:
                        outfile.write('{0:s}\n{1:s}\n'.format(k,v))

    logger.info('Catenate {0:s} and {1:s}...'.format(gff1, gff2))
    cgff = os.path.join(tmpdir, 'cat.gff')
    with open(cgff, "w") as outfile:
        for catfile in [gff1, gff2]:
            with open(catfile, 'rb') as fd:
                shutil.copyfileobj(fd, outfile)
    bdb = '{0:s}_{1:s}'.format(out2, 'cds.fa')
    logger.info('Make blastDB for CDS sequences from {0:s}...'.format(bdb))
    subprocess.Popen([makeblastdb_path, '-in', bdb, '-dbtype', 'nucl']).wait()
    print('\n')
    logger.info('Sequence alignment for cds fasta files between {0:s} and {1:s}...'.format(gff1, gff2))
    binput = '{0:s}_{1:s}'.format(out1, 'cds.fa')
    bout = os.path.join(tmpdir, 'blastn.out')
    subprocess.Popen([blastn_path, '-db', bdb, '-query', binput,'-out', bout, '-evalue', '1e-10', '-penalty', '-15', '-ungapped', '-outfmt', '6']).wait()
    logger.info('Find CDS matched pairs between {0:s} and {1:s}...'.format(gff1, gff2))
    cmd = os.path.join(lib_path, 'auto_assignment', 'find_match.pl')
    report1 = os.path.join(tmpdir, 'report1.txt')
    subprocess.Popen(['perl', cmd, cgff, bout, scode, report1, out1_type]).wait()

    with open(bout, "r") as bcds:
        for line in bcds:
            try:
                QueryID = re.match("^.*ID=([^|]+).+$",line.split("\t")[0]).group(1)
                transcripts.discard(QueryID)
            except:
                pass
    if len(transcripts) >0:
        if user_defined2 == None:
            bdb = '{0:s}_{1:s}'.format(out2, 'trans.fa')
        else:
            bdb = '{0:s}_{1:s}'.format(out2, 'cds.fa')
            logger.info('Make blastDB for transcript sequences from {0:s}...'.format(bdb))
        subprocess.Popen([makeblastdb_path, '-in', bdb, '-dbtype', 'nucl']).wait()
        print('\n')
        logger.info('Sequence alignment for transcript fasta files between {0:s} and {1:s}...'.format(gff1, gff2))
        subprocess.Popen([blastn_path, '-db', bdb, '-query', binput,'-out', bout, '-evalue', '1e-10', '-penalty', '-15', '-ungapped', '-outfmt', '6']).wait()

        logger.info('Find transcript matched pairs between {0:s} and {1:s}...'.format(gff1, gff2))
        cmd = os.path.join(lib_path, 'auto_assignment', 'find_match.pl')
        report1_trans = os.path.join(tmpdir, 'report1_trans.txt')
        subprocess.Popen(['perl', cmd, cgff, bout, scode, report1_trans, out1_type]).wait()

        with open(report1,"a") as rep1:
            with open(report1_trans,"r") as rep1_trans:
                for line in rep1_trans:
                    try:
                        transID = line.split("\t")[2]
                        if transID in transcripts:
                            rep1.write(line)
                    except:
                        pass
    bdb = '{0:s}_{1:s}'.format(out2, 'pre_trans.fa')
    logger.info('Make blastDB for premature transcript sequences from {0:s}...'.format(bdb))
    subprocess.Popen([makeblastdb_path, '-in', bdb, '-dbtype', 'nucl']).wait()
    print('\n')
    logger.info('Sequence alignment for premature transcript fasta files between {0:s} and {1:s}...'.format(gff1, gff2))
    binput = '{0:s}_{1:s}'.format(out1, 'pre_trans.fa')
    bout = os.path.join(tmpdir, 'blastn.out')
    subprocess.Popen([blastn_path, '-db', bdb, '-query', binput,'-out', bout, '-evalue', '1e-10', '-penalty', '-15', '-ungapped', '-outfmt', '6']).wait()

    cmd = os.path.join(lib_path, 'auto_assignment', 'find_match.pl')
    logger.info('Find premature transcript matched pairs between {0:s} and {1:s}...'.format(gff1, gff2))
    report2 = os.path.join(tmpdir, 'report2.txt')
    subprocess.Popen(['perl', cmd, cgff, bout, scode, report2, out1_type]).wait()

    print('\n')
    cmd = os.path.join(lib_path, 'auto_assignment', 'gen_spreadsheet.pl')
    check1 = os.path.join(outdir, 'check1.txt')
    logger.info('Generate {0:s} for Check Point 1 internal reviewing...'.format(check1))
    subprocess.Popen(['perl', cmd, summary, report1, report2, check1]).wait()


if __name__ == '__main__':
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
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=dedent("""\
    Extract sequences from specific regions of genome based on gff file.
    Testing enviroment:
    1. Python 2.7

    Inputs:
    1. GFF3: reads from STDIN by default, may specify the file name with the -g argument
    2. fasta file: reads from STDIN by default, may specify the file name with the -f argument

    Outputs:
    1. Extract sequences from specific regions of genome based on gff file.

    """))
    parser.add_argument('-g1', '--gff1', type=str, help='GFF for curated gene annotations from Apollo (default: STDIN)')
    parser.add_argument('-g2', '--gff2', type=str, help='GFF for predicted gene models or previous official gene set (default: STDIN)')
    parser.add_argument('-f', '--fasta', type=str, help='FASTA for genome sequences (default: STDIN)')
    parser.add_argument('-s', '--species_code', type=str, help ='Species code used in I5K WorkSapce@NAL')
    parser.add_argument('-o', '--output_dir', type=str, help='Output directory (default: STDIN)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()

    if args.gff1:
        logger_stderr.info('Checking gff file (%s)...', args.gff1)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff1 = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.gff2:
        logger_stderr.info('Checking gff file (%s)...', args.gff2)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.gff2 = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    if args.fasta:
        logger_stderr.info('Checking genome fasta (%s)...', args.fasta)
    elif not sys.stdin.isatty(): # if STDIN connected to pipe or file
        args.fasta = sys.stdin
        logger_stderr.info('Reading from STDIN...')
    else: # no input
        parser.print_help()
        sys.exit(1)

    args.species_code='TEMP'
    if args.species_code:
        logger_stderr.info('Specifying species code (%s)...', args.species_code)

    outdir = './auto_replace_tag'
    if args.output_dir:
        outdir = '{0:s}/{1:s}'.format('.', args.output_dir)

    main(args.gff1, args.gff2, args.fasta, outdir, args.species_code, logger_stderr)
