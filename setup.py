"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from distutils.command.build import build
# To use a consistent encoding
from codecs import open
from os import path, remove, mkdir
import shutil
import tarfile
import urllib
import platform
import sys
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


here = path.abspath(path.dirname(__file__))


class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        # Mark us as not a pure python package
        self.root_is_pure = False

class CustomBuildCommand(build):
    def run(self):
        platform_system = platform.system(
        )  # Linux: Linux; Mac:Darwin; Windows: Windows

        blast_path = path.join(here, 'gff3tool', 'lib', 'ncbi-blast+')
        blast_file = path.join(blast_path, 'blast.tgz')

        mkdir(blast_path)

        if platform_system == 'Linux':
            urllib.urlretrieve(
                'https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.2.31/ncbi-blast-2.2.31+-x64-linux.tar.gz',
                blast_file)
        elif platform_system == 'Windows':
            urllib.urlretrieve(
                'https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.2.31/ncbi-blast-2.2.31+-x64-win64.tar.gz',
                blast_file)
        elif platform_system == 'Darwin':
            urllib.urlretrieve(
                'https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.2.31/ncbi-blast-2.2.31+-universal-macosx.tar.gz',
                blast_file)
        else:
            sys.error(
                'GFF3 Toolkit currently only supports linux, windows, and MacOS'
            )

        tar = tarfile.open(blast_file, 'r:gz')
        tar.extractall(blast_path)
        tar.close()

        extract_path = path.join(blast_path, 'ncbi-blast-2.2.31+')
        shutil.move(path.join(extract_path, 'bin'), blast_path)
        if path.exists(blast_file):
            remove(blast_file)
        if path.exists(extract_path):
            shutil.rmtree(extract_path)

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = {}
with open(path.join(here, 'gff3tool', 'bin', 'version.py')) as fp:
    exec (fp.read(), version)

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install bcinfo
    #
    # And where it will live on PyPI: https://pypi.org/project/bcinfo/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name='gff3tool',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version['__version__'],  # Required

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='Python programs for processing GFF3 files',  # Required

    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',
    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url='https://github.com/NAL-i5K/GFF3toolkit',  # Optional

    # This should be your name or the name of the organization which owns the
    # project.
    author='NAL i5k workspace',  # Optional

    # This should be a valid email address corresponding to the author listed
    # above.
    author_email='i5k@ars.usda.gov',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        # Pick your license as you wish
        'License :: Public Domain',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords='gff3 gff bioinformatics ',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required

    cmdclass={
        'build': CustomBuildCommand,
        'bdist_wheel': bdist_wheel
    },

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    extras_require={  # Optional
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    package_data={  # Optional
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],  # Optional

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={  # Optional
        'console_scripts': [
            'gff3_fix=gff3tool.bin.gff3_fix:script_main',
            'gff3_merge=gff3tool.bin.gff3_merge:script_main',
            'gff3_QC=gff3tool.bin.gff3_QC:script_main',
            'gff3_sort=gff3tool.bin.gff3_sort:script_main',
            'gff3_to_fasta=gff3tool.bin.gff3_to_fasta:script_main'
        ]
    },
    include_package_data=True, # include other files
    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/NAL-i5K/GFF3toolkit/issues',
        'Source': 'https://github.com/NAL-i5K/GFF3toolkit',
    },
)
