"""Compatibility setup.py that keeps custom BLAST bundling hooks."""

from setuptools import setup, find_packages
try:
    from setuptools.command.build import build
except ImportError:
    from setuptools._distutils.command.build import build
from os import path, remove, mkdir
import hashlib
import platform
import shutil
import tarfile
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

try:
    from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


here = path.abspath(path.dirname(__file__))
BLAST_VERSION = '2.17.0'


def _blast_archive_name(version, platform_system):
    if platform_system == 'Linux':
        return 'ncbi-blast-{0:s}+-x64-linux.tar.gz'.format(version)
    if platform_system == 'Windows':
        return 'ncbi-blast-{0:s}+-x64-win64.tar.gz'.format(version)
    if platform_system == 'Darwin':
        return 'ncbi-blast-{0:s}+-universal-macosx.tar.gz'.format(version)
    raise RuntimeError('GFF3 Toolkit currently only supports Linux, Windows, and MacOS')


def bundle_blast(project_root, version):
    platform_system = platform.system()
    archive_name = _blast_archive_name(version, platform_system)

    blast_path = path.join(project_root, 'gff3tool', 'lib', 'ncbi-blast+')
    blast_file = path.join(blast_path, 'blast.tgz')
    blast_md5_file = path.join(blast_path, 'blast.tgz.md5')
    blast_bin_path = path.join(blast_path, 'bin')
    base_url = 'https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/{0:s}/{1:s}'.format(
        version, archive_name)
    download_url = base_url
    download_md5_url = base_url + '.md5'

    if path.exists(blast_bin_path):
        return

    if not path.exists(blast_path):
        mkdir(blast_path)

    urlretrieve(download_url, blast_file)
    urlretrieve(download_md5_url, blast_md5_file)
    _verify_download_md5(blast_file, blast_md5_file, archive_name)

    tar = tarfile.open(blast_file, 'r:gz')
    try:
        _safe_extract_tar(tar, blast_path)
    finally:
        tar.close()

    extract_path = path.join(blast_path, 'ncbi-blast-{0:s}+'.format(version))
    shutil.move(path.join(extract_path, 'bin'), blast_path)

    if path.exists(blast_file):
        remove(blast_file)
    if path.exists(blast_md5_file):
        remove(blast_md5_file)
    if path.exists(extract_path):
        shutil.rmtree(extract_path)


def _verify_download_md5(archive_path, md5_path, archive_name):
    with open(md5_path, 'r') as md5_handle:
        md5_line = md5_handle.readline().strip()

    if not md5_line:
        raise RuntimeError('BLAST MD5 file is empty: {0:s}'.format(md5_path))

    tokens = md5_line.split()
    expected_md5 = tokens[0].lower()
    if len(expected_md5) != 32 or any(ch not in '0123456789abcdef' for ch in expected_md5):
        raise RuntimeError('Invalid MD5 value in BLAST checksum file: {0:s}'.format(md5_line))

    # Format is typically: <md5> <filename>
    if len(tokens) > 1 and archive_name not in md5_line:
        raise RuntimeError('BLAST checksum file does not reference expected archive: {0:s}'.format(archive_name))

    actual_md5 = hashlib.md5()
    with open(archive_path, 'rb') as archive_handle:
        while True:
            chunk = archive_handle.read(1024 * 1024)
            if not chunk:
                break
            actual_md5.update(chunk)

    actual_md5_hex = actual_md5.hexdigest().lower()
    if actual_md5_hex != expected_md5:
        raise RuntimeError(
            'BLAST download checksum mismatch for {0:s}: expected {1:s}, got {2:s}'.format(
                archive_name,
                expected_md5,
                actual_md5_hex,
            )
        )


def _safe_extract_tar(archive, destination):
    destination_root = path.realpath(destination)
    if not destination_root.endswith(path.sep):
        destination_root = destination_root + path.sep

    safe_members = []
    for member in archive.getmembers():
        if path.isabs(member.name):
            raise RuntimeError('Refusing to extract absolute tar member: {0:s}'.format(member.name))
        if member.issym() or member.islnk():
            raise RuntimeError('Refusing to extract linked tar member: {0:s}'.format(member.name))

        member_path = path.realpath(path.join(destination, member.name))
        if not member_path.startswith(destination_root):
            raise RuntimeError('Refusing to extract outside destination: {0:s}'.format(member.name))
        safe_members.append(member)

    archive.extractall(destination, members=safe_members)


class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False

class CustomBuildCommand(build):
    def run(self):
        bundle_blast(here, BLAST_VERSION)
        super(CustomBuildCommand, self).run()

setup(
    cmdclass={
        'build': CustomBuildCommand,
        'bdist_wheel': bdist_wheel
    },
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'tests.*']),
    include_package_data=True,
)
