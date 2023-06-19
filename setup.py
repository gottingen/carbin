#
# Copyright 2023 The Turbo Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from setuptools import setup, find_packages
import os, re, sys

def get_version(package):
    """Return package version as listed in `__version__` in `init.py`."""
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

def get_requires(filename):
    requirements = []
    with open(filename) as req_file:
        for line in req_file.read().splitlines():
            if not line.strip().startswith("#"):
                requirements.append(line)
    return requirements

project_requirements = get_requires("requirements.txt")

if os.name == 'posix' and sys.version_info[0] < 3: project_requirements.append('subprocess32')

setup(
    name="carbin",
    version=get_version("carbin"),
    url='https://github.com/gottingen/carbin',
    license='boost',
    description='Cmake package retrieval',
    author='Jeff li',
    author_email='bohuli2048@gmial.com',
    packages=find_packages(),
    package_data={'cmake': ['*.cmake']},
    install_requires=project_requirements,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'carbin = carbin.cli:cli',
        ]
    },
    zip_safe=False
)
