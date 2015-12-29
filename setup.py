import os
import setuptools

GITHUB_URL = 'https://github.com/datascopeanalytics/traces'

try:
    import pypandoc
except ImportError:
    pypandoc = None


def read_version():
    """Parse the package __init__ file to find the version so that it's
    not in multiple places.

    """
    filename = os.path.join("traces", "__init__.py")
    version = None
    with open(filename) as stream:
        for line in stream:
            if "VERSION" in line:
                version = line.split('=')[-1].strip().replace("'", "")

    # throw error if version isn't in __init__ file
    if version is None:
        raise ValueError('must define VERSION in %s' % filename)
                
    return version

def read_description():
    """Read in the description from README and convert to RST for pypi if
    the pypandoc package is available.

    """
    with open("README.md") as stream:
        md = stream.read()
        if pypandoc:
            long_description = \
                pypandoc.convert(md, 'rst', format='markdown_github')
        else:
            long_description = md

    return long_description

def read_dependencies():
    """Read in the dependencies from the virtualenv requirements file.

    """
    dependencies = []
    with open('requirements/python.txt', 'r') as stream:
        for line in stream:
            package = line.strip().split('#')[0].strip()
            if package:
                dependencies.append(package)

setuptools.setup(
    name='traces',
    version=read_version(),
    description="Tools for analysis of unevenly space time series.",
    long_description=read_description(),
    url=GITHUB_URL,
    download_url="%s/archives/master" % GITHUB_URL,
    author='Mike Stringer',
    author_email='mike.stringer@datascopeanalytics.com',
    license='MIT',
    packages=[
        'traces',
    ],
    install_requires=read_dependencies(),
    zip_safe=False,
)
