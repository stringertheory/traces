#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup


def read_init(key):
    """Parse the package __init__ file to find a variable so that it's not
    in multiple places.

    """
    filename = os.path.join("traces", "__init__.py")
    result = None
    with open(filename) as stream:
        for line in stream:
            if key in line:
                result = line.split('=')[-1].strip().replace("'", "")

    # throw error if version isn't in __init__ file
    if result is None:
        raise ValueError('must define %s in %s' % (key, filename))

    return result


def read_author():
    return read_init('author')


def read_author_email():
    return read_init('email')


def read_dependencies(filename):
    """Read in the dependencies from the virtualenv requirements file.

    """
    dependencies = []
    filepath = os.path.join('requirements', filename)
    with open(filepath, 'r') as stream:
        for line in stream:
            package = line.strip().split('#')[0].strip()
            if package and package.split(' ')[0] != '-r':
                dependencies.append(package)
    return dependencies


setup(
    name='traces',
    version='0.4.0',
    description="A library for unevenly-spaced time series analysis.",
    long_description=("View on github: "  # string continuation, not a tuple
                      "https://github.com/datascopeanalytics/traces"),
    author=read_author(),
    author_email=read_author_email(),
    url='https://github.com/datascopeanalytics/traces',
    packages=['traces'],
    package_dir={'traces': 'traces'},
    include_package_data=True,
    install_requires=read_dependencies('python.txt'),
    extras_require={
        'test': read_dependencies('python-test.txt'),
        'doc': read_dependencies('python-doc.txt'),
        'dev': read_dependencies('python-dev.txt'),
        'pandas': ['pandas'],
    },
    license="MIT license",
    zip_safe=False,
    keywords='traces',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='nose.collector',
)
