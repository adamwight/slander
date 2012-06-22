#!/usr/bin/env python
'''
Push feed and vcs activities to an IRC channel.  Configured with the ".slander" rc file, or another yaml file specified on the cmd line.

CREDITS
Miki Tebeka, http://pythonwise.blogspot.com/2009/05/subversion-irc-bot.html
Eloff, http://stackoverflow.com/a/925630
rewritten by Adam Wight,
project homepage is https://github.com/adamwight/slander

EXAMPLE
This is the configuration file used for the CiviCRM project:
    jobs:
        svn:
            root: http://svn.civicrm.org/civicrm
            args: --username SVN_USER --password SVN_PASSS
            changeset_url_format:
                https://fisheye2.atlassian.com/changelog/CiviCRM?cs=%s
        jira:
            base_url:
                http://issues.civicrm.org/jira
            source:
                http://issues.civicrm.org/jira/activity?maxResults=20&streams=key+IS+CRM&title=undefined

    irc:
        host: irc.freenode.net
        port: 6667
        nick: civi-activity
        realname: CiviCRM svn and jira notification bot
        channel: "#civicrm" #note that quotes are necessary here
        maxlen: 200

    poll_interval: 60

    project_url: https://svn.civicrm.org/tools/trunk/bin/scripts/ircbot-civi.py
'''

from irc import RelayToIRC
from job import JobQueue

import sys
import os

# pip install pyyaml
import yaml


def load_config(path):
    dotfile = os.path.expanduser(path)
    if os.path.exists(dotfile):
        print "Reading config from %s" % (dotfile, )
        return yaml.load(file(dotfile))

def parse_args(args):
    if len(args) == 2:
        search_paths = [
            args[1],
            "~/.slander-" + args[1],
            "/etc/slander-" + args[1],
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

    global test
    test = False
    if "test" in config:
        test = config["test"]

    return config

if __name__ == "__main__":
    RelayToIRC.run(parse_args(sys.argv))
