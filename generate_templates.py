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

import requests
import yaml
from jinja2 import Environment, FileSystemLoader


def get_project_vars(project_name):
    project_vars = init_vars.copy()

    vars_url = "https://raw.githubusercontent.com/linuxserver/docker-{}/master/readme-vars.yml".format(
        project_name)
    response = requests.get(vars_url)
    project_vars.update(yaml.load(response.text, Loader=yaml.FullLoader))

    # overrides
    project_vars["project_blurb"] = project_vars["project_blurb"].replace(
        "{{ project_name|capitalize }}", project_vars["project_name"].capitalize())
    project_vars["project_blurb"] = project_vars["project_blurb"].replace(
        "{{ project_name }}", project_vars["project_name"].capitalize())
    project_vars["project_blurb"] = project_vars["project_blurb"].replace(
        "{{ project_url }}", project_vars["project_url"])
    project_vars["project_blurb"] = project_vars["project_blurb"].replace(
        "\n", " ")
    project_vars["project_blurb"] = project_vars["project_blurb"].replace(
        '"', "'")
    project_vars["project_blurb"] = ' '.join(
        project_vars["project_blurb"].split())

    for row in project_vars["common_param_env_vars"]:
        if row["env_var"] == "PGID":
            row["env_value"] = 100
            row["desc"] = "for UserID"
        if row["env_var"] == "PUID":
            row["env_value"] = 1024
            row["desc"] = "for GroupID"

    for row in project_vars["param_env_vars"]:
        if row["env_var"] == "TZ":
            row["env_value"] = "Europe/Amsterdam"
            row["desc"] = "Specify a timezone to use for example Europe/Amsterdam"

    if project_vars["project_logo"] != "" and requests.get(project_vars["project_logo"]).status_code != 200:
        project_vars["project_logo"] = ""

    if "full_custom_readme" in project_vars.keys() and project_vars["full_custom_readme"] != "":
        project_vars["project_blurb"] = "This container needs special attention. Please check https://hub.docker.com/r/linuxserver/{} for details.".format(
            project_vars["project_name"])

    return project_vars


vars_url = "https://raw.githubusercontent.com/linuxserver/docker-jenkins-builder/master/vars/common"
resp = requests.get(vars_url)
init_vars = yaml.load(resp.text, Loader=yaml.FullLoader)

vars_url = "https://raw.githubusercontent.com/linuxserver/docker-jenkins-builder/master/vars/_container-vars-blank"
resp = requests.get(vars_url)
init_vars.update(yaml.load(resp.text, Loader=yaml.FullLoader))

env = Environment(loader=FileSystemLoader(
    "templates"), trim_blocks=True, lstrip_blocks=True)
env.globals.update(get_project_vars=get_project_vars)
template = env.get_template("templates-2.0.j2")

image_url = "https://fleet.linuxserver.io/api/v1/images"
response = requests.get(image_url)
response_json = response.json()
project_list = response_json["data"]["repositories"]["linuxserver"]

# # testing
# project_list = list(
#     filter(lambda project: project["name"] == "sonarr", project_list))

projects = {
    "projects": project_list
}

out_filename = "templates-2.0.json"
with open(out_filename, "w") as out_file:
    out_file.write(template.render(projects))

# check valid json
with open(out_filename) as in_file:
    templates_v2 = json.load(in_file)

# check filesize
if os.path.getsize(out_filename) < 200000:
    raise Exception

out_filename = "templates-1.20.0.json"
templates_v1 = json.dumps(templates_v2["templates"], indent=4)
with open(out_filename, "w") as out_file:
    out_file.write(templates_v1)
