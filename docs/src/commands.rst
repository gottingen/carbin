
========
Commands
========

-----
build
-----

.. program:: build

This will build a package, but it doesn't install it. This is useful over using raw cmake as it will use the cmake toolchain that was initialized by carbin which sets cmake up to easily find the dependencies that have been installed by carbin. This will also install the dependencies in a ``dev-requirements.txt`` file if available, otherwise it will install any dependencies in the ``requirements.txt``.

.. option:: <package-source>

This specifies the package source (see :ref:`pkg-src`) that will be built.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

.. option::  -B, --build-path PATH  

    Set the path for the build directory to use when building the package.

.. option::  -t, --test             

    Test package after building. This will set the ``BUILD_TESTING`` cmake variable to true. It will first try to run the ``check`` target. If that fails it will call ``ctest`` to try to run the tests.

.. option::  -c, --configure        

    Configure cmake. This will run either ``ccmake`` or ``cmake-gui`` so the cmake variables can be set.

.. option::  -C, --clean            

    Remove build directory.

.. option::  -P, --path             

    Show path to build directory.

.. option::  -D, --define VAR=VALUE      

    Extra configuration variables to pass to CMake

.. option::  -T, --target TARGET      

    Cmake target to build.

.. option::  -y, --yes

    Affirm all questions.

.. option::  -G, --generator GENERATOR   

    Set the generator for CMake to use.

.. option::  --debug

    Build the debug version of the package.

.. option::  --release

    Build the release version of the package.

-----
clean
-----

.. program:: clean

This will clear the directory used by carbin. This will remove all packages that have been installed, and any toolchain settings.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

.. option:: -y, --yes

    Affirm all questions.

------
ignore
------

.. program:: ignore

This will ignore a package, so if an install command or a dependency requests the package it will be treated as already installed. This is useful to ignore a dependency that may already be installed by the system.

.. option:: <package-name>

    This is the name of the package that will be ignored.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

----
init
----

.. program:: init

This will initialize the cmake toolchain. By default, the ``install`` command will initialize a cmake toolchain if one doesn't exists. This allows setting different variable, such as setting C++ compiler or standard version.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

.. option::  -B, --build-path PATH  

    Set the path for the build directory to use when building the package.

.. option::  -t, --toolchain FILE   

    Set cmake toolchain file to use.

.. option::  --cc COMPILER             

    Set c compiler.

.. option::  --cxx COMPILER             

    Set c++ compiler.

.. option::  --cflags FLAGS        

    Set additional c flags.

.. option::  --cxxflags FLAGS        

    Set additional c++ flags.

.. option::  --ldflags FLAGS         

    Set additional linker flags.

.. option::  --std TEXT             

    Set C++ standard if available.

.. option::  -D, --define VAR=VALUE      

    Extra configuration variables to pass to CMake.

.. option::  --shared               

    Set toolchain to build shared libraries by default.

.. option::  --static               

    Set toolchain to build static libraries by default.


-------
install
-------

.. program:: install

A package can be installed using the ``install`` command. When a package is installed, ``carbin`` configures a build directory with cmake, and then builds the ``all`` target and the ``install`` target. So, essentially, ``carbin`` will run the equivalent of these commands on the package to install it::

    mkdir build
    cd build
    cmake -DCMAKE_TOOLCHAIN_FILE=$CARBIN_PREFIX/carbin/carbin.cmake -DCMAKE_INSTALL_PREFIX=$CARBIN_PREFIX ..
    cmake --build .
    cmake --build . --target install

However, ``carbin`` will always create the build directory out of source. The ``carbin.cmake`` is a toolchain file that is setup by ``carbin``, so that cmake can find the installed packages. Other setting can be added about the toolchain as well(see :ref:`init`).

.. option:: <package-source>

    This specifies the package source (see :ref:`pkg-src`) that will be installed. If no package source is provided then ``carbin`` will default to using the ``requirements.txt`` file or the ``dev-requirements.txt`` file if available. That is ``carbin install`` is equivalent to ``carbin install -f requirements.txt`` or ``carbin install -f dev-requirements.txt``.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

.. option::  -B, --build-path PATH  

    Set the path for the build directory to use when building the package.

.. option::  -U, --update           

    Update package. This will rebuild the package even its already installed and replace it with the newly built package.

.. option::  -t, --test             

    Test package before installing. This will set the ``BUILD_TESTING`` cmake variable to true. It will first try to run the ``check`` target. If that fails it will call ``ctest`` to try to run the tests.

.. option::  --test-all             

    Test all packages including its dependencies before installing by running ctest or check target.

.. option::  -f, --file FILE        

    Install packages listed in the file.

.. option::  -D, --define VAR=VALUE      

    Extra configuration variables to pass to CMake.

.. option::  -G, --generator GENERATOR   

    Set the generator for CMake to use.

.. option::  -X, --cmake

    This specifies an alternative cmake file to be used to build the library. This is useful for packages that don't have a cmake file.

.. option::  --debug

    Install the debug version of the package.

.. option::  --release

    Install the release version of the package.

----
list
----

.. program:: list

This will list all packages that have been installed.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

----------
pkg-config
----------

.. program:: pkg-config

This will run pkg-config, but will search in the carbin directory for pkg-config files. This useful for finding dependencies when not using cmake.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

------
remove
------

.. program:: remove

This will remove a package. If other packages depends on the package to be removed, those packages will be removed as well.

.. option:: <package-name>

    This is the name of the package to be removed.

.. option::  -p, --prefix PATH      

    Set prefix where packages are installed. This defaults to a directory named ``carbin`` in the current working directory. This can also be overridden by the ``CARBIN_PREFIX`` environment variable.

.. option::  -v, --verbose          

    Enable verbose mode.

.. option:: -y, --yes

    Affirm all questions.

.. option:: -A, --all

    Select all packages installed.

.. option:: -U, --unlink

    Unlink the package but don't remove it. The ``install`` command can be used to relink the package. 
