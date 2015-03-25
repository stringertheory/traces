import setuptools

import traces

# read in the description from README
with open("README.md") as stream:
    long_description = stream.read()

github_url='https://github.com/datascopeanalytics/traces'

# read in the dependencies from the virtualenv requirements file
dependencies = []
with open('requirements.txt', 'r') as stream:
    for line in stream:
        package = line.strip().split('#')[0]
        if package:
            dependencies.append(package)

setuptools.setup(
    name=traces.__name__,
    version=traces.VERSION,
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
