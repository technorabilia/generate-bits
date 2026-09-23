# Portainer App Templates for LinuxServer.io Docker containers
# Copyright (C) 2021  Technorabilia
# Written by Simon de Kraa <simon@technorabilia.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os

from jinja2 import Environment, FileSystemLoader

import common

init_vars = common.get_initial_variables()
project_list = common.get_project_list()

env = Environment(loader=FileSystemLoader(
    "templates"), trim_blocks=True, lstrip_blocks=True)
env.globals.update(init_vars=init_vars)
env.globals.update(get_project_vars=common.get_project_vars)
template = env.get_template("templates.j2")

projects = {
    "projects": project_list
}

out_filename = "templates.json"
with open(out_filename, "w") as out_file:
    out_file.write(template.render(projects))

# check valid json
with open(out_filename) as in_file:
    templates = json.load(in_file)

# check filesize
if os.path.getsize(out_filename) < 200000:
    raise Exception
