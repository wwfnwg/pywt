#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys
import subprocess
from functools import partial

from setuptools import setup, Extension
from numpy import get_include as get_numpy_include
from distutils.sysconfig import get_python_inc

try:
    from Cython.Build import cythonize
except ImportError:
    USE_CYTHON = False
else:
    USE_CYTHON = True

MAJOR = 0
MINOR = 5
MICRO = 0
ISRELEASED = False
VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)


# Return the git revision as a string
def git_version():
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        GIT_REVISION = out.strip().decode('ascii')
    except OSError:
        GIT_REVISION = "Unknown"

    return GIT_REVISION


def get_version_info():
    # Adding the git rev number needs to be done inside
    # write_version_py(), otherwise the import of pywt.version messes
    # up the build under Python 3.
    FULLVERSION = VERSION
    if os.path.exists('.git'):
        GIT_REVISION = git_version()
    elif os.path.exists('pywt/version.py'):
        # must be a source distribution, use existing version file
        # load it as a separate module to not load pywt/__init__.py
        import imp
        version = imp.load_source('pywt.version', 'pywt/version.py')
        GIT_REVISION = version.git_revision
    else:
        GIT_REVISION = "Unknown"

    if not ISRELEASED:
        FULLVERSION += '.dev0+' + GIT_REVISION[:7]

    return FULLVERSION, GIT_REVISION


def write_version_py(filename='pywt/version.py'):
    cnt = """
# THIS FILE IS GENERATED FROM PYWAVELETS SETUP.PY
short_version = '%(version)s'
version = '%(version)s'
full_version = '%(full_version)s'
git_revision = '%(git_revision)s'
release = %(isrelease)s

if not release:
    version = full_version
"""
    FULLVERSION, GIT_REVISION = get_version_info()

    with open(filename, 'w') as a:
        a.write(cnt % {'version': VERSION,
                       'full_version': FULLVERSION,
                       'git_revision': GIT_REVISION,
                       'isrelease': str(ISRELEASED)})


# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')


if sys.platform == "darwin":
    # Don't create resource files on OS X tar.
    os.environ["COPY_EXTENDED_ATTRIBUTES_DISABLE"] = "true"
    os.environ["COPYFILE_DISABLE"] = "true"


make_ext_path = partial(os.path.join, "pywt", "_extensions")

sources = ["c/common.c", "c/convolution.c", "c/wt.c", "c/wavelets.c"]
sources = list(map(make_ext_path, sources))
source_templates = ["c/convolution.template.c", "c/wt.template.c"]
source_templates = list(map(make_ext_path, source_templates))
headers = ["c/templating.h", "c/wavelets_coeffs.h",
            "c/common.h", "c/convolution.h", "c/wt.h", "c/wavelets.h"]
headers = list(map(make_ext_path, headers))
header_templates = ["c/convolution.template.h", "c/wt.template.h",
                    "c/wavelets_coeffs.template.h"]
header_templates = list(map(make_ext_path, header_templates))

cython_modules = ['_pywt', '_dwt', '_swt']
cython_sources = [('{0}.pyx' if USE_CYTHON else '{0}.c').format(module)
                  for module in cython_modules]

c_macros = [("PY_EXTENSION", None)]
cython_macros = []
cythonize_opts = {}
if os.environ.get("CYTHON_TRACE"):
    cythonize_opts['linetrace'] = True
    cython_macros.append(("CYTHON_TRACE_NOGIL", 1))

# By default C object files are rebuilt for every extension
# C files must be built once only for coverage to work
c_lib = ('c_wt', {'sources': sources,
                  'depends': source_templates + header_templates + headers,
                  'include_dirs': [make_ext_path("c"), get_python_inc()],
                  'macros': c_macros,})

ext_modules = [
    Extension('pywt._extensions.{0}'.format(module),
              sources=[make_ext_path(source)],
              include_dirs=[make_ext_path("c"), get_numpy_include()],
              define_macros=c_macros + cython_macros,
              libraries=[c_lib[0]],)
    for module, source, in zip(cython_modules, cython_sources)
]

if __name__ == '__main__':
    # Rewrite the version file everytime
    write_version_py()

    if USE_CYTHON:
        ext_modules = cythonize(ext_modules, compiler_directives=cythonize_opts)

    setup(
        name="PyWavelets",
        maintainer="The PyWavelets Developers",
        maintainer_email="http://groups.google.com/group/pywavelets",
        url="https://github.com/PyWavelets/pywt",
        download_url="https://github.com/PyWavelets/pywt/releases",
        license="MIT",
        description="PyWavelets, wavelet transform module",
        long_description="""\
        PyWavelets is a Python wavelet transforms module that includes:

        * 1D and 2D Forward and Inverse Discrete Wavelet Transform (DWT and IDWT)
        * 1D and 2D Stationary Wavelet Transform (Undecimated Wavelet Transform)
        * 1D and 2D Wavelet Packet decomposition and reconstruction
        * Computing Approximations of wavelet and scaling functions
        * Over seventy built-in wavelet filters and support for custom wavelets
        * Single and double precision calculations
        * Results compatibility with Matlab Wavelet Toolbox (tm)
        """,
        keywords=["wavelets", "wavelet transform", "DWT", "SWT", "scientific"],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Intended Audience :: Education",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: C",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Topic :: Software Development :: Libraries :: Python Modules"
        ],
        platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
        version=get_version_info()[0],

        packages=['pywt', 'pywt._extensions', 'pywt.data'],
        package_data={'pywt.data': ['*.npy', '*.npz']},
        ext_modules=ext_modules,
        libraries=[c_lib],
        test_suite='nose.collector',

        # A function is imported in setup.py, so not really useful
        install_requires=["numpy"],
    )
