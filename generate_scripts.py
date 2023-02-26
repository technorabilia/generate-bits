# Docker scripts for LinuxServer.io Docker containers
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

import os
import textwrap

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
    project_vars["param_container_name"] = project_vars["param_container_name"].replace(
        "{{ project_name }}", project_vars["project_name"])

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

    lines = textwrap.wrap(
        project_vars["project_blurb"], 78, break_long_words=False)
    project_vars["project_blurb"] = ""
    for line in lines:
        project_vars["project_blurb"] += "# {}\n".format(line)

    for row in project_vars["common_param_env_vars"]:
        if row["env_var"] == "PGID":
            row["env_value"] = "${PGID:-100}"
            row["desc"] = "for GroupID"
        if row["env_var"] == "PUID":
            row["env_value"] = "${PUID:-1024}"
            row["desc"] = "for UserID"
        if row["env_var"] == "TZ":
            row["env_value"] = "${TZ:-Europe/Amsterdam}"            

    for row in project_vars["param_env_vars"]:
        if row["env_var"] == "TZ":
            project_vars["param_env_vars"].remove(row)
    if len(project_vars["param_env_vars"]) == 0:
        project_vars["param_usage_include_env"] = False

    if project_vars["project_logo"] == "http://www.logo.com/logo.png":
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
    "templates"), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
env.globals.update(get_project_vars=get_project_vars)

image_url = "https://fleet.linuxserver.io/api/v1/images"
response = requests.get(image_url)
response_json = response.json()
project_list = response_json["data"]["repositories"]["linuxserver"]

# # testing
# project_list = list(
#     filter(lambda project: project["name"] == "sonarr", project_list))

project_list = list(
    filter(lambda project: project["deprecated"] == False, project_list))

projects = {
    "projects": project_list
}

out_basedir = "./lsio"
os.makedirs(out_basedir, exist_ok=True)
with open("{}/docker-env.cfg".format(out_basedir), "w") as out_file:
    out_file.write('''#BASEDIR=/volume1/docker
#PUID=1024
#PGID=100
#TZ=Europe/Amsterdam
''')

for project in project_list:
    print(project["name"])

    project_vars = get_project_vars(project["name"])
    if project_vars["project_name"] == "name":
        continue

    out_dir = "{}/{}".format(out_basedir, project["name"])
    os.makedirs(out_dir, exist_ok=True)

    template = env.get_template("docker-run.j2")
    with open("{}/docker-run.sh".format(out_dir), "w") as out_file:
        out_file.write(template.render(project_vars=project_vars))

    template = env.get_template("docker-compose.j2")
    with open("{}/docker-compose.yaml".format(out_dir), "w") as out_file:
        out_file.write(template.render(project_vars=project_vars))

    template = env.get_template("run-once.j2")
    with open("{}/run-once.sh".format(out_dir), "w") as out_file:
        out_file.write(template.render(project_vars=project_vars))
