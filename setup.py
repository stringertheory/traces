import os
import setuptools

import pypandoc

with open(os.path.join("traces", "__init__.py")) as stream:
    for line in stream:
        if "VERSION" in line:
            version = line.split('=')[-1].strip().replace("'","")

# read in the description from README and convert to RST for pypi
with open("README.md") as stream:
    md = stream.read()
    long_description = pypandoc.convert(md, 'rst', format='markdown_github')
    
github_url='https://github.com/datascopeanalytics/traces'

# read in the dependencies from the virtualenv requirements file
dependencies = []
with open('requirements/python.txt', 'r') as stream:
    for line in stream:
        package = line.strip().split('#')[0]
        if package:
            dependencies.append(package)

setuptools.setup(
    name='traces',
    version=version,
    description="Tools for analysis of unevenly space time series.",
    long_description=long_description,
    url=github_url,
    download_url="%s/archives/master" % github_url,
    author='Mike Stringer',
    author_email='mike.stringer@datascopeanalytics.com',
    license='MIT',
    packages=[
        'traces',
    ],
    install_requires=dependencies,
    zip_safe=False,
)
