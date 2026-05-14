"""Compatibility setup.py that keeps custom BLAST bundling hooks."""

from setuptools import setup, find_packages
from distutils.command.build import build
from os import path, remove, mkdir
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
    download_url = 'https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/{0:s}/{1:s}'.format(
        version, archive_name)

    if not path.exists(blast_path):
        mkdir(blast_path)

    urlretrieve(download_url, blast_file)

    tar = tarfile.open(blast_file, 'r:gz')
    tar.extractall(blast_path)
    tar.close()

    extract_path = path.join(blast_path, 'ncbi-blast-{0:s}+'.format(version))
    shutil.move(path.join(extract_path, 'bin'), blast_path)

    if path.exists(blast_file):
        remove(blast_file)
    if path.exists(extract_path):
        shutil.rmtree(extract_path)


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
