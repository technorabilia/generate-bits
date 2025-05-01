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

import textwrap

import requests
import yaml


def get_project_vars(project_name, init_vars, mode):
    project_vars = init_vars.copy()

    vars_url = "https://raw.githubusercontent.com/linuxserver/docker-{}/master/readme-vars.yml".format(
        project_name)
    response = requests.get(vars_url)
    project_vars.update(yaml.load(response.text, Loader=yaml.FullLoader))

    # overrides
    if mode == "scripts":
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

    if mode == "scripts":
        lines = textwrap.wrap(
            project_vars["project_blurb"], 78, break_long_words=False)
        project_vars["project_blurb"] = ""
        for line in lines:
            project_vars["project_blurb"] += "# {}\n".format(line)

    for row in project_vars["common_param_env_vars"]:
        if row["env_var"] == "PGID":
            row["desc"] = "Run 'id [USER]' for the owner of the host volume directories to get the GID to use here."
        if row["env_var"] == "PUID":
            row["desc"] = "Run 'id [USER]' for the owner of the host volume directories to get the UID to use here."

    if project_vars["project_logo"] == "http://www.logo.com/logo.png":
        project_vars["project_logo"] = ""

    if "full_custom_readme" in project_vars.keys() and project_vars["full_custom_readme"] != "":
        project_vars["project_blurb"] = "# This container needs special attention. Please check https://hub.docker.com/r/linuxserver/{} for details.".format(
            project_vars["project_name"])

    return project_vars


def get_initial_variables():
    vars_url = "https://raw.githubusercontent.com/linuxserver/docker-jenkins-builder/master/ansible/vars/common.yml"
    resp = requests.get(vars_url)
    init_vars = yaml.load(resp.text, Loader=yaml.FullLoader)
    
    vars_url = "https://raw.githubusercontent.com/linuxserver/docker-jenkins-builder/master/ansible/vars/_container-vars-blank"
    resp = requests.get(vars_url)
    init_vars.update(yaml.load(resp.text, Loader=yaml.FullLoader))

    init_vars["param_env_vars"] = [row for row in init_vars["param_env_vars"] if row["env_var"] != "TZ"]
    if not init_vars["param_env_vars"]:
        init_vars["param_usage_include_env"] = False

    return init_vars


def get_project_list():
    image_url = "https://api.linuxserver.io/api/v1/images"
    response = requests.get(image_url)
    response_json = response.json()
    project_list = response_json["data"]["repositories"]["linuxserver"]

    project_list = list(
        filter(lambda project: not project["deprecated"], project_list))

    # # testing
    # project_list = list(
    #     filter(lambda project: project["name"] == "emby", project_list))

    return project_list
