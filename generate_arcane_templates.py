# Arcane Registry Template for LinuxServer.io Docker containers
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

import hashlib
import json
import re

from jinja2 import Environment, FileSystemLoader

import common

DOCKER_BITS_RAW_URL = "https://raw.githubusercontent.com/technorabilia/docker-bits/refs/heads/main/lsio"
DOCKER_BITS_TREE_URL = "https://github.com/technorabilia/docker-bits/tree/main/lsio"


def slugify(project_name):
    # A handful of LSIO project names (e.g. "changedetection.io",
    # "your_spotify") contain characters the id slug pattern disallows.
    # compose_url/env_url/documentation_url still use the real project_name
    # since that matches the actual docker-bits directory name.
    return re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")


init_vars = common.get_initial_variables()
project_list = common.get_project_list()

env = Environment(loader=FileSystemLoader(
    "templates"), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
compose_template = env.get_template("docker-compose.j2")

templates = []

for project in project_list:
    print(project["name"])

    project_vars = common.get_project_vars(
        project["name"], init_vars, mode="scripts")
    if project_vars["project_name"] == "name":
        continue

    project_name = project_vars["project_name"].lower()

    # docker-compose.j2 renders identically to what generate_docker_bits.py writes
    # to lsio/<project>/docker-compose.yaml, so hashing it here matches the
    # file that ends up published to docker-bits.
    compose_content = compose_template.render(project_vars=project_vars)
    content_hash = hashlib.sha256(compose_content.encode("utf-8")).hexdigest()

    # mode="scripts" wraps the blurb as "# "-prefixed comment lines; unwrap
    # it back into plain text for the JSON description field.
    description = " ".join(
        line.lstrip("# ") for line in project_vars["project_blurb"].splitlines())

    tags = [
        tag.strip().replace(" ", "-")
        for tag in project.get("category", "").split(",") if tag.strip()
    ] or ["linuxserver"]

    templates.append({
        "id": slugify(project_name),
        "name": project_name.capitalize(),
        "description": description,
        "version": "1.0.0",
        "author": "technorabilia",
        "compose_url": "{}/{}/docker-compose.yaml".format(DOCKER_BITS_RAW_URL, project_name),
        "env_url": "{}/docker-env.cfg".format(DOCKER_BITS_RAW_URL),
        "documentation_url": "{}/{}".format(DOCKER_BITS_TREE_URL, project_name),
        "content_hash": content_hash,
        "tags": tags,
    })

registry = {
    "$schema": "https://registry.getarcane.app/schema.json",
    "name": "Technorabilia LinuxServer.io Templates",
    "description": "Arcane templates for LinuxServer.io Docker containers, based on data provided by LinuxServer.io.",
    "author": "technorabilia",
    "url": "https://github.com/technorabilia/docker-bits",
    "version": "1.0.0",
    "templates": templates,
}

out_filename = "templates.json"
with open(out_filename, "w") as out_file:
    json.dump(registry, out_file, indent=2)
    out_file.write("\n")

# check valid json
with open(out_filename) as in_file:
    json.load(in_file)
