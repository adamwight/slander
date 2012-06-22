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

from xml.etree.cElementTree import parse as xmlparse
from cStringIO import StringIO
from subprocess import Popen, PIPE

#pip install feedparser
import feedparser
from HTMLParser import HTMLParser

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

class SvnPoller(object):
    """
    Run "svn info" and "svn log -r REV" to get metadata for the most recent commits.
    """

    def __init__(self, root=None, args=None, changeset_url_format=None):
        self.pre = ["svn", "--xml"] + args.split()
        self.root = root
        self.changeset_url_format = changeset_url_format
        print "Initializing SVN poller: %s" % (" ".join(self.pre)+" "+root, )

    def svn(self, *cmd):
        pipe = Popen(self.pre +  list(cmd) + [self.root], stdout=PIPE)
        try:
            data = pipe.communicate()[0]
        except IOError:
            data = ""
        return xmlparse(StringIO(data))

    def revision(self):
        tree = self.svn("info")
        revision = tree.find(".//commit").get("revision")
        return int(revision)

    def revision_info(self, revision):
        revision = str(revision)
        tree = self.svn("log", "-r", revision)
        author = tree.find(".//author").text
        comment = truncate(strip(tree.find(".//msg").text))
        url = self.changeset_url(revision)

        return (revision, author, comment, url)

    def changeset_url(self, revision):
        return self.changeset_url_format % (revision, )

    previous_revision = None
    def check(self):
        try:
            latest = self.revision()
            if self.previous_revision and latest != self.previous_revision:
                for rev in range(self.previous_revision + 1, latest + 1):
                    yield "r%s by %s: %s -- %s" % self.revision_info(rev)
            self.previous_revision = latest
        except Exception, e:
            print "ERROR: %s" % e


class FeedPoller(object):
    """
    Generic RSS/Atom feed watcher
    """
    last_seen_id = None

    def __init__(self, source=None):
        print "Initializing feed poller: %s" % (source, )
        self.source = source

    def check(self):
        result = feedparser.parse(self.source)
        result.entries.reverse()
        for entry in result.entries:
            if (not self.last_seen_id) or (self.last_seen_id == entry.id):
                if not test:
                    break
            yield self.parse(entry)

        if result.entries:
            self.last_seen_id = result.entries[0].id

    def parse(self, entry):
        return "%s [%s]" % (entry.summary, entry.link)


class JiraPoller(FeedPoller):
    """
    Polls a Jira RSS feed and formats changes to issue trackers.
    """
    def __init__(self, base_url=None, **kw):
        self.base_url = base_url
        super(JiraPoller, self).__init__(**kw)

    def parse(self, entry):
        m = re.search(r'(CRM-[0-9]+)$', entry.link)
        if (not m) or (entry.generator_detail.href != self.base_url):
            return
        issue = m.group(1)
        summary = truncate(strip(entry.summary))
        url = "%s/browse/%s" % (self.base_url, issue)

        return "%s: %s %s -- %s" % (entry.author_detail.name, issue, summary, url)

class MinglePoller(FeedPoller):
    """
    Format changes to Mingle cards
    """
    def parse(self, entry):
        m = re.search(r'^(.*/([0-9]+))', entry.id)
        url = m.group(1)
        issue = int(m.group(2))
        author = abbrevs(entry.author_detail.name)

        assignments = []
        details = entry.content[0].value
        assignment_phrases = [
            r'(?P<property>[^,>]+) set to (?P<value>[^,<]+)',
            r'(?P<property>[^,>]+) changed from (?P<previous_value>[^,<]+) to (?P<value>[^,<]+)',
        ]
        for pattern in assignment_phrases:
            for m in re.finditer(pattern, details):
                normal_form = None
                if re.match(r'\d{4}/\d{2}/\d{2}|\(not set\)', m.group('value')):
                    pass
                elif re.match(r'Planning - Sprint', m.group('property')):
                    n = re.search(r'(Sprint \d+)', m.group('value'))
                    normal_form = "->" + n.group(1)
                else:
                    normal_form = abbrevs(m.group('property')+" : "+m.group('value'))

                if normal_form:
                    assignments.append(normal_form)
        summary = '|'.join(assignments)

        # TODO 'Description changed'
        for m in re.finditer(r'(?P<property>[^:>]+): (?P<value>[^<]+)', details):
            if m.group('property') == 'Comment added':
                summary = m.group('value')+" "+summary

        summary = truncate(summary)

        return "#%d: (%s) %s -- %s" % (issue, author, summary, url)

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
        classname = type_name.capitalize() + "Poller"
        klass = globals()[classname]
        job = klass(**options)
        job.config = options
        job.config['class'] = type_name
        jobs.append(job)
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
