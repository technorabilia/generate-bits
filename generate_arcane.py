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

import datetime
import hashlib
import json
import re

import common
import render

DOCKER_BITS_RAW_URL = "https://raw.githubusercontent.com/technorabilia/docker-bits/refs/heads/main/lsio"
DOCKER_BITS_TREE_URL = "https://github.com/technorabilia/docker-bits/tree/main/lsio"


def to_semver(raw_version, fallback="0.0.0"):
    # LSIO's "version" (e.g. "4.0.19.2979-ls324", "10.3_p1-r1-ls236",
    # "b93769c4-ls53") is whatever the upstream project + LSIO build tag
    # happen to produce, not semver. The Arcane schema requires a strict
    # MAJOR.MINOR.PATCH, so take the first up-to-three numeric components
    # as major/minor/patch and preserve everything else (extra numeric
    # components, the LSIO build suffix, non-numeric versions entirely) as
    # semver build metadata rather than discarding it.
    raw_version = (raw_version or "").strip()
    if not raw_version:
        return fallback

    match = re.match(r"^v?(\d+(?:\.\d+)*)(.*)$", raw_version)
    if not match:
        build = _sanitize_build(raw_version)
        return "{}+{}".format(fallback, build) if build else fallback

    core, rest = match.groups()
    parts = [str(int(p)) for p in core.split(".")]
    major, minor, patch = (parts + ["0", "0"])[:3]
    extras = parts[3:]

    rest = re.sub(r"^[-+.]+", "", rest.strip())
    build_bits = [b for b in (extras + [rest]) if b]
    build_bits = [_sanitize_build(b) for b in build_bits]
    build_bits = [b for b in build_bits if b]

    version = "{}.{}.{}".format(major, minor, patch)
    if build_bits:
        version += "+" + ".".join(build_bits)
    return version


def _sanitize_build(value):
    # Build metadata only allows [0-9a-zA-Z-] between dots.
    value = re.sub(r"[^0-9a-zA-Z.-]", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip(".-")


def slugify(project_name):
    # A handful of LSIO project names (e.g. "changedetection.io",
    # "your_spotify") contain characters the id slug pattern disallows.
    # compose_url/env_url/documentation_url still use the real project_name
    # since that matches the actual docker-bits directory name.
    return re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")


init_vars = common.get_initial_variables()
project_list = common.get_project_list()

templates = []

for project in project_list:
    print(project["name"])

    project_vars = common.get_project_vars(
        project["name"], init_vars, mode="scripts")
    if project_vars["project_name"] == "name":
        continue

    project_name = project_vars["project_name"].lower()

    # render_docker_compose renders identically to what generate_scripts.py
    # writes to lsio/<project>/docker-compose.yaml, so hashing it here
    # matches the file that ends up published to docker-bits.
    compose_content = render.render_docker_compose(project_vars)
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
        "version": to_semver(project.get("version")),
        "author": "technorabilia",
        "compose_url": "{}/{}/docker-compose.yaml".format(DOCKER_BITS_RAW_URL, project_name),
        "env_url": "{}/docker-env.cfg".format(DOCKER_BITS_RAW_URL),
        "documentation_url": "{}/{}".format(DOCKER_BITS_TREE_URL, project_name),
        "content_hash": content_hash,
        "tags": tags,
    })

today = datetime.date.today()
# Content is re-pulled from live LSIO metadata on every run, so the registry
# version tracks the generation date rather than a hand-bumped release number.
registry_version = "{}.{}.{}".format(today.year, today.month, today.day)

registry = {
    "$schema": "https://registry.getarcane.app/schema.json",
    "name": "Technorabilia LinuxServer.io Templates",
    "description": "Arcane templates for LinuxServer.io Docker containers, based on data provided by LinuxServer.io.",
    "author": "technorabilia",
    "url": "https://github.com/technorabilia/docker-bits",
    "version": registry_version,
    "templates": templates,
}

out_filename = "templates.json"
with open(out_filename, "w") as out_file:
    json.dump(registry, out_file, indent=2)
    out_file.write("\n")

# check valid json
with open(out_filename) as in_file:
    json.load(in_file)
