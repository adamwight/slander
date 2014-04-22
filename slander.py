#!/usr/bin/env python
'''Entrypoint'''

from irc import RelayToIRC

import sys
import os

import yaml

def load_config(path):
    dotfile = os.path.expanduser(path)
    if os.path.exists(dotfile):
        print "Reading config from %s" % (dotfile, )
        return yaml.load(file(dotfile))

def parse_args(args):
    if len(args) == 2:
        search_paths = [
            # Raw filename
            args[1],
            # or project name
            "~/.slander-{project}".format(project=args[1]),
            "/etc/slander/{project}.yaml".format(project=args[1]),
        ]
    else:
        search_paths = [
            "~/.slander",
            "/etc/slander",
        ]
    for path in search_paths:
        config = load_config(path)
        if config:
            break

    if not config:
        sys.exit(args[0] + ": No config!")

    # normalize some stuff :(
    if "source_url" not in config:
        config["source_url"] = "https://github.com/adamwight/slander"

    global test
    test = False
    if "test" in config:
        test = config["test"]

    return config

if __name__ == "__main__":
    RelayToIRC.run(parse_args(sys.argv))
