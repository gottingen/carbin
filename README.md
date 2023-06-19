carbin
====

the carbin tool from[cget](https://github.com/pfultz2/cget), Just as `cget` did an excellent job and provided me with a lot of help. At the same time, 
I have different needs and design ideas, so I copied him and developed on his basis to meet my mind. I place the 'cget' in project root dir.
Cmake package retrieval. This can be used to download and install cmake packages. The advantages of using `carbin` are:

* provide cmake template easy to build a project, see `carbin` `create`
* Non-intrusive: There is no need to write special hooks in cmake to use `carbin`. One cmake file is written and can be used to install a package with `carbin` or standalone.
* Works out of the box: Since it uses the standard build and install of cmake, it already works with almost all cmake packages. There is no need to wait for packages to convert over to support `carbin`. Standard cmake packages can be already installed immediately.
* Decentralized: Packages can be installed from anywhere, from github, urls, or local files.

Getting carbin
------------
`carbin` can be simply installed using `pip`(you can get pip from [here](https://pip.pypa.io/en/stable/installing/)):

    pip install carbin

Or installed directly with python:

    python setup.py install

On windows, you may want to install pkgconfig-lite to support packages that use pkgconfig. This can be installed with `carbin` as well:

    carbin install pfultz2/pkgconfig

Quickstart
----------
We can create a `cmake` build system by `carbin`
```shell
    carbin create --test --benchmark --examples --requirements
```
We can also install cmake packages directly from source files, for example zlib:

```shell
    carbin install http://zlib.net/zlib-1.2.11.tar.gz
```
However, its much easier to install recipes so we don't have to remember urls:

    carbin install pfultz2/carbin-recipes

Then we can install packages such as boost:

    carbin install boost

Or curl:

    carbin install curl

Documentation
-------------

See [here](http://carbin.readthedocs.io/) for the latest documentation.


Supported platforms
-------------------

This is supported on python 3.8 or higher. 

