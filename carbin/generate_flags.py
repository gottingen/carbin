#
#  Copyright 2023 The carbin Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from os import path
import sys


# Helper functions
def file_header_lines():
  return "GENERATED! DO NOT MANUALLY EDIT THIS FILE."


def flatten(*lists):
  return [item for sublist in lists for item in sublist]


def relative_filename(filename):
  return path.join(path.dirname(__file__), filename)


# Style classes.  These contain all the syntactic styling needed to generate a
# copt file for different build tools.
class CMakeStyle(object):
  """Style object for CMake copts file."""

  def separator(self):
    return ""

  def list_introducer(self, name):
    return "list(APPEND " + name

  def list_closer(self):
    return ")\n"

  def docstring(self):
    return "\n".join((("# " + line).strip() for line in file_header_lines()))

  def filename(self):
    return "GENERATED_TurboCopts.cmake"


class StarlarkStyle(object):
  """Style object for Starlark copts file."""

  def separator(self):
    return ","

  def list_introducer(self, name):
    return name + " = ["

  def list_closer(self):
    return "]\n"

  def docstring(self):
    docstring_quotes = "\"\"\""
    return docstring_quotes + "\n".join(
        flatten(file_header_lines(), [docstring_quotes]))

  def filename(self):
    return "GENERATED_copts.bzl"


def copt_list(name, arg_list, style):
  """Copt file generation."""

  make_line = lambda s: "    \"" + s + "\"" + style.separator()
  external_str_list = [make_line(s) for s in arg_list]

  return "\n".join(
      flatten(
          [style.list_introducer(name)],
          external_str_list,
          [style.list_closer()]))


def generate_copt_file(vars, style):
  """Creates a generated copt file using the given style object.

  Args:
    style: either StarlarkStyle() or CMakeStyle()
  """
  with open(relative_filename(style.filename()), "w") as f:
    f.write(style.docstring())
    f.write("\n")
    for var_name, arg_list in sorted(vars.items()):
      f.write("\n")
      f.write(copt_list(var_name, arg_list, style))

