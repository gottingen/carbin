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
import click


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cmd(ctx, debug):
    ctx.obj['DEBUG'] = debug
    print(id(ctx.obj))
    print(id(ctx))


@cmd.command(name="init")
@click.pass_context
def init_cmd(ctx):
    click.echo('Debug is %s' % (ctx.obj['DEBUG'] and 'on' or 'off'))
    print(id(ctx.obj))
    print(id(ctx))
    print(id(ctx.parent))


@cmd.command(name="build")
@click.pass_context
def build_cmd(ctx):
    click.echo('Debug is %s' % (ctx.obj['DEBUG'] and 'on' or 'off'))
    print(id(ctx.obj))
    print(id(ctx))
    print(id(ctx.parent))


if __name__ == '__main__':
    cmd(obj={})
