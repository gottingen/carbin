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
import os, shutil, shlex, six, inspect, click, contextlib, sys, functools, re

from carbin.builder import Builder
from carbin.package import fname_to_pkg
from carbin.package import PackageSource
from carbin.package import PackageBuild
from carbin.package import parse_pkg_build_tokens
import carbin.util as util
from carbin.types import returns
from carbin.types import params

__CARBIN_DIR__ = os.path.dirname(os.path.realpath(__file__))
__CARBIN_CMAKE_DIR__ = os.path.join(__CARBIN_DIR__, 'cmake')


@params(s=six.string_types)
def parse_deprecated_alias(s):
    i = s.find(':', 0, max(s.find('://'), s.find(':\\')))
    if i > 0:
        click.echo("WARNING: Using ':' for aliases is now deprecated.")
        return s[0:i], s[i + 1:]
    else:
        return None, s


@params(s=six.string_types)
def parse_alias(s):
    i = s.find(',')
    if i > 0:
        return s[0:i], s[i + 1:]
    else:
        return parse_deprecated_alias(s)


@params(s=six.string_types)
def parse_src_name(url, default=None):
    x = url.split('@')
    p = x[0]
    # If the same name is used, then reduce to the same name
    if '/' in p:
        ps = p.split('/')
        if functools.reduce(lambda x, y: x == y, ps):
            p = ps[0]
    v = default
    if len(x) > 1: v = x[1]
    return (p, v)


def cmake_set(var, val, quote=True, cache=None, description=None):
    x = val
    if quote: x = util.quote(val)
    if cache is None or cache.lower() == 'none':
        yield "set({0} {1})".format(var, x)
    else:
        yield 'set({0} {1} CACHE {2} "{3}")'.format(var, x, cache, description or '')


def cmake_append(var, *vals, **kwargs):
    quote = True
    if 'quote' in kwargs: quote = kwargs['quote']
    x = ' '.join(vals)
    if quote: x = ' '.join([util.quote(val) for val in vals])
    yield 'list(APPEND {0} {1})'.format(var, x)


def cmake_if(cond, *args):
    yield 'if ({})'.format(cond)
    for arg in args:
        for line in arg:
            yield '    ' + line
    yield 'endif()'


def cmake_else(*args):
    yield 'else ()'
    for arg in args:
        for line in arg:
            yield '    ' + line


def parse_cmake_var_type(key, value):
    if ':' in key:
        p = key.split(':')
        return (p[0], p[1].upper(), value)
    elif value.lower() in ['on', 'off', 'true', 'false']:
        return (key, 'BOOL', value)
    else:
        return (key, 'STRING', value)


def find_cmake(p, start):
    if p and not os.path.isabs(p):
        absp = util.actual_path(p, start)
        if os.path.exists(absp):
            return absp
        else:
            x = util.carbin_dir('cmake', p)
            if os.path.exists(x):
                return x
            elif os.path.exists(x + '.cmake'):
                return x + '.cmake'
    return p


PACKAGE_SOURCE_TYPES = (six.string_types, PackageSource, PackageBuild)


class CarbinPrefix:
    def __init__(self, prefix, verbose=False, build_path=None):
        self.prefix = os.path.abspath(prefix or 'carbin')
        self.verbose = verbose
        self.build_path_var = build_path
        self.cmd = util.Commander(paths=[self.get_path('bin')], env=self.get_env(), verbose=self.verbose)
        self.toolchain = self.write_cmake()

    def log(self, *args):
        if self.verbose: click.secho(' '.join([str(arg) for arg in args]), bold=True)

    def check(self, f, *args):
        if self.verbose and not f(*args):
            raise util.BuildError('ASSERTION FAILURE: ', ' '.join([str(arg) for arg in args]))

    def get_env(self):
        return {
            'LD_LIBRARY_PATH': self.get_path('lib'),
            'PKG_CONFIG_PATH': self.pkg_config_path()
        }

    def write_cmake(self, always_write=False, **kwargs):
        return util.mkfile(self.get_private_path(), 'carbin.cmake', self.generate_cmake_toolchain(**kwargs),
                           always_write=always_write)

    @returns(inspect.isgenerator)
    @util.yield_from
    def generate_cmake_toolchain(self, toolchain=None, cc=None, cxx=None, cflags=None, cxxflags=None, ldflags=None,
                                 std=None, defines=None):
        set_ = cmake_set
        if_ = cmake_if
        else_ = cmake_else
        append_ = cmake_append
        yield set_('CARBIN_PREFIX', self.prefix)
        yield set_('CMAKE_PREFIX_PATH', self.prefix)
        yield if_('${CMAKE_VERSION} VERSION_LESS "3.6.0"',
                  ['include_directories(SYSTEM ${CARBIN_PREFIX}/include)'],
                  else_(
                      set_('CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES', '${CARBIN_PREFIX}/include'),
                      set_('CMAKE_C_STANDARD_INCLUDE_DIRECTORIES', '${CARBIN_PREFIX}/include')
                  )
                  )
        if toolchain: yield ['include({})'.format(util.quote(os.path.abspath(toolchain)))]
        yield if_('CMAKE_CROSSCOMPILING',
                  append_('CMAKE_FIND_ROOT_PATH', self.prefix)
                  )
        yield if_('CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT',
                  set_('CMAKE_INSTALL_PREFIX', self.prefix)
                  )
        if cxx: yield set_('CMAKE_CXX_COMPILER', cxx)
        if cc: yield set_('CMAKE_C_COMPILER', cc)
        if std:
            yield if_('NOT "${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC"',
                      set_('CMAKE_CXX_STD_FLAG', "-std={}".format(std))
                      )
        yield if_('"${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC"',
                  set_('CMAKE_CXX_ENABLE_PARALLEL_BUILD_FLAG', "/MP")
                  )
        if cflags:
            yield set_('CMAKE_C_FLAGS', "$ENV{{CFLAGS}} ${{CMAKE_C_FLAGS_INIT}} {}".format(cflags or ''),
                       cache='STRING')
        if cxxflags or std:
            yield set_('CMAKE_CXX_FLAGS',
                       "$ENV{{CXXFLAGS}} ${{CMAKE_CXX_FLAGS_INIT}} ${{CMAKE_CXX_STD_FLAG}} {}".format(cxxflags or ''),
                       cache='STRING')
        if ldflags:
            for link_type in ['STATIC', 'SHARED', 'MODULE', 'EXE']:
                yield set_('CMAKE_{}_LINKER_FLAGS'.format(link_type), "$ENV{{LDFLAGS}} {0}".format(ldflags),
                           cache='STRING')
        for dkey in defines or {}:
            name, vtype, value = parse_cmake_var_type(dkey, defines[dkey])
            yield set_(name, value, cache=vtype, quote=(vtype != 'BOOL'))
        yield if_('BUILD_SHARED_LIBS',
                  set_('CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS', 'ON', cache='BOOL')
                  )
        yield set_('CMAKE_FIND_FRAMEWORK', 'LAST', cache='STRING')
        yield set_('CMAKE_INSTALL_RPATH', '${CARBIN_PREFIX}/lib', cache='STRING')

    def get_path(self, *paths):
        return os.path.join(self.prefix, *paths)

    def get_private_path(self, *paths):
        return self.get_path('carbin', *paths)

    def get_public_path(self, *paths):
        return self.get_path('etc', 'carbin', *paths)

    def get_recipe_paths(self):
        return [self.get_public_path('recipes')]

    def get_builder_path(self, *paths):
        if self.build_path_var:
            return os.path.join(self.build_path_var, *paths)
        else:
            return self.get_private_path('build', *paths)

    @contextlib.contextmanager
    def create_builder(self, name, tmp=False):
        pre = ''
        if tmp: pre = 'tmp-'
        d = self.get_builder_path(pre + name)
        exists = os.path.exists(d)
        util.mkdir(d)
        yield Builder(self, d, exists)
        if tmp: shutil.rmtree(d, ignore_errors=True)

    def get_package_directory(self, *dirs):
        return self.get_private_path('pkg', *dirs)

    def get_unlink_directory(self, *dirs):
        return self.get_private_path('unlink', *dirs)

    def get_deps_directory(self, name, *dirs):
        return self.get_package_directory(name, 'deps', *dirs)

    def get_unlink_deps_directory(self, name, *dirs):
        return self.get_unlink_directory(name, 'deps', *dirs)

    def parse_src_file(self, name, url, start=None):
        f = util.actual_path(url, start)
        self.log('parse_src_file actual_path:', start, f)
        if os.path.exists(f): return PackageSource(name=name, url='file://' + f)
        return None

    def parse_src_recipe(self, name, url):
        p, v = parse_src_name(url)
        for rpath in self.get_recipe_paths():
            rp = os.path.normcase(os.path.join(rpath, p, v or ''))
            if os.path.exists(rp):
                return PackageSource(name=name or p, recipe=rp)
        return None

    def parse_src_github(self, name, url):
        p, v = parse_src_name(url, 'HEAD')
        if '/' in p:
            url = 'https://github.com/{0}/archive/{1}.tar.gz'.format(p, v)
        else:
            url = 'https://github.com/{0}/{0}/archive/{1}.tar.gz'.format(p, v)
        if name is None: name = p
        return PackageSource(name=name, url=url)

    @returns(PackageSource)
    @params(pkg=PACKAGE_SOURCE_TYPES)
    def parse_pkg_src(self, pkg, start=None, no_recipe=False):
        if isinstance(pkg, PackageSource): return pkg
        if isinstance(pkg, PackageBuild): return self.parse_pkg_src(pkg.pkg_src, start)
        name, url = parse_alias(pkg)
        self.log('parse_pkg_src:', name, url, pkg)
        if '://' not in url:
            return self.parse_src_file(name, url, start) or \
                (None if no_recipe else self.parse_src_recipe(name, url)) or \
                self.parse_src_github(name, url)
        return PackageSource(name=name, url=url)

    @returns(PackageBuild)
    @params(pkg=PACKAGE_SOURCE_TYPES)
    def parse_pkg_build(self, pkg, start=None, no_recipe=False):
        if isinstance(pkg, PackageBuild):
            pkg.pkg_src = self.parse_pkg_src(pkg.pkg_src, start, no_recipe)
            if pkg.pkg_src.recipe: pkg = self.from_recipe(pkg.pkg_src.recipe, pkg)
            if pkg.cmake: pkg.cmake = find_cmake(pkg.cmake, start)
            return pkg
        else:
            pkg_src = self.parse_pkg_src(pkg, start, no_recipe)
            if pkg_src.recipe:
                return self.from_recipe(pkg_src.recipe, pkg_src.name)
            else:
                return PackageBuild(pkg_src)

    def from_recipe(self, recipe, pkg=None, name=None):
        recipe_pkg = os.path.join(recipe, "package.txt")
        util.ensure_exists(recipe_pkg)
        p = next(iter(self.from_file(recipe_pkg, no_recipe=True)))
        self.check(lambda: p.pkg_src is not None)
        requirements = os.path.join(recipe, "carbin_deps.txt")
        if os.path.exists(requirements): p.requirements = requirements
        p.pkg_src.recipe = None
        # Use original name
        if pkg:
            p.pkg_src.name = pkg.pkg_src.name
        elif name:
            p.pkg_src.name = name

        if pkg:
            return p.merge(pkg)
        else:
            return p

    def from_file(self, file, url=None, no_recipe=False):
        if file is None:
            return
        if not os.path.exists(file):
            self.log("file not found: " + file)
            return
        start = os.path.dirname(file)
        if url is not None and url.startswith('file://'):
            start = url[7:]
        with open(file) as f:
            self.log("parse file: " + file)
            cache_line = ""
            for line in f.readlines():
                if str.endswith(line, '\\\n'):
                    if line.lstrip().startswith('#'):
                        continue
                    cache_line = cache_line + line.strip('\\\n')
                    continue
                cache_line = cache_line + line
                tokens = shlex.split(cache_line, comments=True)
                cache_line = ""
                if len(tokens) > 0:
                    pb = parse_pkg_build_tokens(tokens)
                    ps = self.from_file(util.actual_path(pb.file, start), no_recipe=no_recipe) if pb.file else [
                        self.parse_pkg_build(pb, start=start, no_recipe=no_recipe)]
                    for p in ps: yield p

    def write_parent(self, pb, track=True):
        if track and pb.parent is not None: util.mkfile(self.get_deps_directory(pb.to_fname()), pb.parent, pb.parent)

    def install_deps(self, pb, d, test=False, test_all=False, generator=None, insecure=False,
                     ignore_requirements=False):
        req_txt = os.path.join(d, 'carbin_deps.txt') if not ignore_requirements else None
        for dependent in self.from_file(pb.requirements or req_txt, pb.pkg_src.url):
            transient = dependent.test or dependent.build
            testing = test or test_all
            installable = not dependent.test or dependent.test == testing
            if installable:
                self.install(dependent.of(pb), test_all=test_all, generator=generator, track=not transient,
                             insecure=insecure)

    @returns(six.string_types)
    @params(pb=PACKAGE_SOURCE_TYPES, test=bool, test_all=bool, update=bool, track=bool)
    def install(self, pb, test=False, test_all=False, generator=None, update=False, track=True, insecure=False):
        pb = self.parse_pkg_build(pb)
        pkg_dir = self.get_package_directory(pb.to_fname())
        unlink_dir = self.get_unlink_directory(pb.to_fname())
        install_dir = self.get_package_directory(pb.to_fname(), 'install')
        # If its been unlinked, then link it in
        if os.path.exists(unlink_dir):
            if update:
                shutil.rmtree(unlink_dir)
            else:
                self.link(pb)
                self.write_parent(pb, track=track)
                return "Linking package {}".format(pb.to_name())
        if os.path.exists(pkg_dir):
            self.write_parent(pb, track=track)
            if update:
                self.remove(pb)
            else:
                return "Package {} already installed".format(pb.to_name())
        with self.create_builder(pb.pkg_src.get_hash(), tmp=True) as builder:
            # Fetch package
            src_dir = builder.fetch(pb.pkg_src.url, pb.hash, (pb.cmake != None), insecure=insecure)
            # Install any dependencies first
            self.install_deps(pb, src_dir, test=test, test_all=test_all, generator=generator, insecure=insecure,
                              ignore_requirements=pb.ignore_requirements)
            # Setup cmake file
            if pb.cmake:
                target = os.path.join(src_dir, 'CMakeLists.txt')
                if os.path.exists(target):
                    os.rename(target, os.path.join(src_dir, builder.cmake_original_file))
                shutil.copyfile(pb.cmake, target)
            # Configure and build
            builder.configure(src_dir, defines=pb.define, generator=generator, install_prefix=install_dir, test=test,
                              variant=pb.variant)
            builder.build(variant=pb.variant)
            # Run tests if enabled
            if test or test_all: builder.test(variant=pb.variant)
            # Install
            builder.build(target='install', variant=pb.variant)
            if util.USE_SYMLINKS:
                util.symlink_dir(install_dir, self.prefix)
            else:
                util.copy_dir(install_dir, self.prefix)
        self.write_parent(pb, track=track)
        return "Successfully installed {}".format(pb.to_name())

    @returns(six.string_types)
    @params(pb=PACKAGE_SOURCE_TYPES)
    def ignore(self, pb):
        pb = self.parse_pkg_build(pb)
        pkg_dir = self.get_package_directory(pb.to_fname())
        # If package doesn't exist
        if not os.path.exists(pkg_dir):
            util.mkfile(pkg_dir, "ignore", "ignore")
            return "Ignore package {}".format(pb.to_name())
        else:
            return "Package {} already installed".format(pb.to_name())

    @params(pb=PACKAGE_SOURCE_TYPES, test=bool)
    def build(self, pb, test=False, target=None, generator=None):
        pb = self.parse_pkg_build(pb)
        src_dir = pb.pkg_src.get_src_dir()
        if os.path.exists(os.path.join(src_dir, 'dev-carbin_deps.txt')):
            pb.requirements = os.path.join(src_dir, 'dev-carbin_deps.txt')
        elif os.path.exists(os.path.join(src_dir, 'carbin_deps.txt')):
            pb.requirements = os.path.join(src_dir, 'carbin_deps.txt')
        with self.create_builder(pb.to_fname()) as builder:
            # Install any dependencies first
            self.install_deps(pb, src_dir, generator=generator, test=test)
            # Configure and build
            if not builder.exists: builder.configure(src_dir, defines=pb.define, generator=generator, test=test,
                                                     variant=pb.variant)
            builder.build(variant=pb.variant, target=target)
            # Run tests if enabled
            if test: builder.test(variant=pb.variant)

    @params(pb=PACKAGE_SOURCE_TYPES)
    def build_path(self, pb):
        pb = self.parse_pkg_build(pb)
        return self.get_builder_path(pb.to_fname(), 'build')

    @params(pb=PACKAGE_SOURCE_TYPES)
    def build_clean(self, pb):
        pb = self.parse_pkg_build(pb)
        p = self.get_builder_path(pb.to_fname())
        if os.path.exists(p): shutil.rmtree(p)

    @params(pb=PACKAGE_SOURCE_TYPES)
    def build_configure(self, pb):
        pb = self.parse_pkg_build(pb)
        src_dir = pb.pkg_src.get_src_dir()
        if 'ccmake' in self.cmd:
            self.cmd.ccmake([src_dir], cwd=self.build_path(pb))
        elif 'cmake-gui' in self.cmd:
            self.cmd.cmake_gui([src_dir], cwd=self.build_path(pb))

    @params(pkg=PACKAGE_SOURCE_TYPES)
    def remove(self, pkg):
        self.unlink(pkg, delete=True)

    @params(pkg=PACKAGE_SOURCE_TYPES)
    def unlink(self, pkg, delete=False):
        pkg = self.parse_pkg_src(pkg)
        pkg_dir = self.get_package_directory(pkg.to_fname())
        unlink_dir = self.get_unlink_directory(pkg.to_fname())
        self.log("Unlink:", pkg_dir)
        if os.path.exists(pkg_dir):
            if util.USE_SYMLINKS:
                util.rm_symlink_from(os.path.join(pkg_dir, 'install'), self.prefix)
            else:
                util.rm_dup_dir(os.path.join(pkg_dir, 'install'), self.prefix, remove_both=False)
            util.rm_empty_dirs(self.prefix)
            if delete:
                util.delete_dir(pkg_dir)
            else:
                util.mkdir(self.get_unlink_directory())
                os.rename(pkg_dir, unlink_dir)

    @params(pkg=PACKAGE_SOURCE_TYPES)
    def link(self, pkg):
        pkg = self.parse_pkg_src(pkg)
        pkg_dir = self.get_package_directory(pkg.to_fname())
        unlink_dir = self.get_unlink_directory(pkg.to_fname())
        if os.path.exists(unlink_dir):
            util.mkdir(self.get_package_directory())
            os.rename(unlink_dir, pkg_dir)
            if util.USE_SYMLINKS:
                util.symlink_dir(os.path.join(pkg_dir, 'install'), self.prefix)
            else:
                util.copy_dir(os.path.join(pkg_dir, 'install'), self.prefix)
        # Relink dependencies
        for dep in util.ls(self.get_unlink_directory(), os.path.isdir):
            ls = util.ls(self.get_unlink_deps_directory(dep), os.path.isfile)
            if pkg.to_fname() in ls: self.link(dep)

    def _list_files(self, pkg=None, top=True):
        if pkg is None:
            return util.ls(self.get_package_directory(), os.path.isdir)
        else:
            p = self.parse_pkg_src(pkg)
            ls = util.ls(self.get_deps_directory(p.to_fname()), os.path.isfile)
            if top:
                return [p.to_fname()] + list(ls)
            else:
                return ls

    def list(self, pkg=None, recursive=False, top=True):
        for d in self._list_files(pkg, top):
            p = fname_to_pkg(d)
            if os.path.exists(self.get_package_directory(d)): yield p
            if recursive:
                for child in self.list(p, recursive=recursive, top=False):
                    yield child

    def clean(self):
        if util.USE_SYMLINKS:
            util.delete_dir(self.get_private_path())
            util.rm_symlink_dir(self.prefix)
            util.rm_empty_dirs(self.prefix)
        else:
            for p in self.list():
                self.remove(p)
            util.delete_dir(self.get_private_path())

    def clean_cache(self):
        p = util.get_cache_path()
        if os.path.exists(p): shutil.rmtree(util.get_cache_path())

    def pkg_config_path(self):
        libs = []
        for p in ['lib', 'lib64', 'share']:
            libs.append(self.get_path(p, 'pkgconfig'))
        return os.pathsep.join(libs)

    @contextlib.contextmanager
    def try_(self, msg=None, on_fail=None):
        try:
            yield
        except util.BuildError as err:
            if err.msg: click.echo(err.msg)
            if msg: click.echo(msg)
            if on_fail: on_fail()
            if self.verbose:
                if err.data: click.echo(err.data)
                raise
            sys.exit(1)
        except:
            extype, exvalue, extraceback = sys.exc_info()
            click.echo("Unexpected error: " + str(extype))
            click.echo(str(exvalue))
            if msg: click.echo(msg)
            if on_fail: on_fail()
            if self.verbose: raise
            sys.exit(1)
