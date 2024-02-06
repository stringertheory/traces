#!/bin/sh

# write all imports that are in non-external-named test files
grep "import " tests/*.py | grep -v "external" > .test_external_deps_imports
# ls tests/*.py | grep -v external | xargs cat | grep "import " | sort | uniq > .test_external_deps_imports

# # go through every value in this and grep
> .test_external_deps_overlap
for i in `poetry show -T --only dev | tr '-' '_' | awk '{print $1}'`; do
    grep $i .test_external_deps_imports >> .test_external_deps_overlap
done;

cat .test_external_deps_overlap | grep -v "\bpytest\b" | sort | uniq
rm -f .test_external_deps_imports .test_external_deps_overlap
