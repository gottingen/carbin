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
import click, os, shutil
import carbin.util as util


class Creater:
    def __init__(self, prefix, name, test, examples, benchmark, requirements):
        self.prefix = prefix
        self.name = name
        self.test = test
        self.examples = examples
        self.benchmark = benchmark
        self.requirements = requirements
        self.top_dir = prefix.get_private_path("cmake")

    def fetch(self):
        util.mkdir(self.top_dir)
        url = 'https://github.com/gottingen/carbin-template/archive/master.tar.gz'
        self.prefix.log("fetch:", url)
        f = util.retrieve_url(url, self.top_dir, copy=True, insecure=True, hash=None)
        if os.path.isfile(f):
            click.echo("Extracting archive {0} ...".format(f))
            util.extract_ar(archive=f, dst=self.top_dir)
        return next(util.get_dirs(self.top_dir))

    def create_project(self):
        d = self.fetch()
        self.copy_project_cmakelist(d)
        self.deal_src_cmakelist(d)
        self.deal_carbin_cmake(d)
        self.deal_cmake(d)
        self.create_example_dir(d)
        self.create_tests_dir(d)
        self.create_benchmark_dir(d)
        self.create_requires_file(d)

    def upgrade_carbin(self):
        d = self.fetch()
        self.deal_carbin_cmake(d)

    def copy_project_cmakelist(self, d):
        p = os.path.join(d, 'CMakeLists.txt')
        fr = open(p, 'r')
        content = fr.read()
        fr.close()
        wc = str.replace(content, "changeme", self.name)
        if not self.test:
            wc = str.replace(wc, "add_subdirectory(tests)", "#add_subdirectory(tests)")

        if not self.benchmark:
            wc = str.replace(wc, "add_subdirectory(benchmark)", "#add_subdirectory(benchmark)")

        if not self.examples:
            wc = str.replace(wc, "add_subdirectory(examples)", "#add_subdirectory(examples)")

        dp = 'CMakeLists.txt'
        fw = open(dp, 'w')
        fw.write(wc)
        fw.close()

    def deal_src_cmakelist(self, d):
        util.mkdir(self.name)
        src = os.path.join(d, 'changeme/CMakeLists.txt')
        util.copy_to(src, self.name)

    def deal_carbin_cmake(self, d):
        if os.path.exists('carbin_cmake'):
            shutil.rmtree('carbin_cmake')
        cm = os.path.join(d, 'carbin_cmake')
        util.copy_dir(cm, 'carbin_cmake')

    ########
    # user's cmake .do not edit
    def deal_cmake(self, d):
        if os.path.exists('cmake'):
            return
        cm = os.path.join(d, 'cmake')
        util.copy_dir(cm, 'cmake')

        if not os.path.exists('conda'):
            cc = os.path.join(d, 'conda')
            util.copy_dir(cc, 'conda')

        src = os.path.join(d, 'changeme/CMakeLists.txt')
        util.copy_to(src, self.name)

    def create_example_dir(self, d):
        if self.examples:
            util.mkdir('examples')
            src = os.path.join(d, 'examples/CMakeLists.txt')
            util.copy_to(src, 'examples')

    def create_tests_dir(self, d):
        if self.test:
            util.mkdir('tests')
            src = os.path.join(d, 'tests/CMakeLists.txt')
            util.copy_to(src, 'tests')

    def create_benchmark_dir(self, d):
        if self.benchmark:
            util.mkdir('benchmark')
            src = os.path.join(d, 'benchmark/CMakeLists.txt')
            util.copy_to(src, 'benchmark')

    def create_requires_file(self, d):
        if not self.requirements:
            return
        if os.path.exists('carbin_deps.txt'):
            return
        src = os.path.join(d, 'carbin_deps.txt')
        if os.path.exists(src):
            util.copy_to(src, '.')
            return
        f = fw = open('carbin_deps.txt', 'w')
        content = '''
#
# Copyright 2023 The titan-search Authors.
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
###########
# turbo
#gottingen/turbo@v0.9.4 -DCARBIN_BUILD_TEST=OFF -DCARBIN_BUILD_BENCHMARK=OFF -DCARBIN_BUILD_EXAMPLES=OFF -DBUILD_SHARED_LIBRARY=OFF -DBUILD_STATIC_LIBRARY=ON -DCMAKE_BUILD_TYPE=release
        '''
        f.write(content)
        f.close()
