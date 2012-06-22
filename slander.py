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

    sourceURL: https://svn.civicrm.org/tools/trunk/bin/scripts/ircbot-civi.py
'''

import sys
import os
import re
import datetime

# pip install pyyaml
import yaml

#pip install twisted twisted.words
from twisted.words.protocols import irc
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

test = False
maxlen = 200
config = None

class RelayToIRC(irc.IRCClient):
    """
    Bot brain will spawn listening jobs and then relay results to an irc channel.
    TODO:
    * separate polling manager from irc protocol
    * operator ACL and commands which perform an action
    """
    sourceURL = "https://github.com/adamwight/slander"
    timestamp = None

    def connectionMade(self):
        self.config = self.factory.config
        self.jobs = create_jobs(self.config["jobs"])
        self.nickname = self.config["irc"]["nick"]
        self.realname = self.config["irc"]["realname"]
        self.channel = self.config["irc"]["channel"]
        global maxlen
        if "maxlen" in self.config["irc"]:
            maxlen = self.config["irc"]["maxlen"]
        if "sourceURL" in self.config:
            self.sourceURL = self.config["sourceURL"]

        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        self.join(self.channel)

    def joined(self, channel):
        print "Joined channel %s as %s" % (channel, self.nickname)
        task = LoopingCall(self.check)
        task.start(self.config["poll_interval"])
        print "Started polling jobs, every %d seconds." % (self.config["poll_interval"], )

    def privmsg(self, user, channel, message):
        if message.find(self.nickname) >= 0:
            if re.search(r'\bhelp\b', message):
                self.say(channel, "If I only had a brain: %s -- Commands: help jobs kill last" % (self.sourceURL, ))
            elif re.search(r'\bjobs\b', message):
                jobs_desc = ", ".join(
                    [("%s: %s" % (j.config['class'], j.config))
                        for j in self.jobs]
                )
                jobs_desc = re.sub(r'p(ass)?w(ord)?[ :=]*[^ ]+', r'p***word', jobs_desc)

                self.say(channel, "Running jobs [%s]" % (jobs_desc, ))
            #elif re.search(r'\bkill\b', message):
            #    self.say(self.channel, "Squeal! Killed by %s" % (user, ))
            #    self.factory.stopTrying()
            #    self.quit()
            elif re.search(r'\blast\b', message):
                if self.timestamp:
                    self.say(channel, "My last post was %s UTC" % (self.timestamp, ))
                else:
                    self.say(channel, "No activity.")
            else:
                print "Failed to handle incoming command: %s said %s" % (user, message)

    def check(self):
        for job in self.jobs:
            for line in job.check():
                if line:
                    if test:
                        print(line)
                    self.say(self.channel, str(line))
                    self.timestamp = datetime.datetime.utcnow()

    @staticmethod
    def run(config):
        factory = ReconnectingClientFactory()
        factory.protocol = RelayToIRC
        factory.config = config
        reactor.connectTCP(config["irc"]["host"], config["irc"]["port"], factory)
        reactor.run()


def strip(text, html=True, space=True):
    class MLStripper(HTMLParser):
        def __init__(self):
            self.reset()
            self.fed = []
        def handle_data(self, d):
            self.fed.append(d)
        def get_data(self):
            return ''.join(self.fed)

    if html:
        stripper = MLStripper()
        stripper.feed(text)
        text = stripper.get_data()
    if space:
        text = re.sub("\s+", " ", text).strip()
    return text

def abbrevs(name):
    """
    Turn a space-delimited name into initials, e.g. Frank Ubiquitous Zappa -> FUZ
    """
    return "".join([w[:1] for w in name.split()])

def truncate(message):
    if len(message) > maxlen:
        return (message[:(maxlen-3)] + "...")
    else:
        return message


def create_jobs(d):
    """
    Read job definitions from a config source, create an instance of the job using its configuration, and store the config for reference.
    """
    jobs = []
    for type_name, options in d.items():
        m = __import__(type_name)
        classname = type_name.capitalize() + "Poller"
        if hasattr(m, classname):
            klass = getattr(m, classname)
            job = klass(**options)
            job.config = options
            job.config['class'] = type_name
            jobs.append(job)
        else:
            sys.exit("Failed to create job of type " + classname)
    return jobs

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

    return config

if __name__ == "__main__":
    RelayToIRC.run(parse_args(sys.argv))
