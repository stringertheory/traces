#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

# TODO: Test setup.py


def read_author():
    """Parse the package __init__ file to find the author so that it's
    not in multiple places.

    """
    filename = os.path.join("traces", "__init__.py")
    author = None
    with open(filename) as stream:
        for line in stream:
            if "author" in line:
                author = line.split('=')[-1].strip().replace("'", "")

    # throw error if version isn't in __init__ file
    if author is None:
        raise ValueError('must define author in %s' % filename)

    return author


def read_author_email():
    """Parse the package __init__ file to find the author email so that it's
    not in multiple places.

    """
    filename = os.path.join("traces", "__init__.py")
    author_email = None
    with open(filename) as stream:
        for line in stream:
            if "email" in line:
                author_email = line.split('=')[-1].strip().replace("'", "")

    # throw error if version isn't in __init__ file
    if author_email is None:
        raise ValueError('must define author email in %s' % filename)

    return author_email


def read_dependencies(filepath):
    """Read in the dependencies from the virtualenv requirements file.

    """
    dependencies = []
    with open(filepath, 'r') as stream:
        for line in stream:
            package = line.strip().split('#')[0].strip()
            if package:
                dependencies.append(package)
    return dependencies


requirements = read_dependencies('requirements/python.txt')

test_requirements = read_dependencies('requirements/python-test.txt')

setup(
    name='traces',
    version='0.1.0',
    description="Traces makes it easy to analyze time series data at irregular intervals.",
    long_description="View on github: https://github.com/datascopeanalytics/traces",
    author=read_author(),
    author_email=read_author_email(),
    url='https://github.com/datascopeanalytics/traces',
    packages=[
        'traces',
    ],
    package_dir={'traces':
                 'traces'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='traces',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='nose.collector',
    tests_require=test_requirements
)
