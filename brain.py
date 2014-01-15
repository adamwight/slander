import re
import json

from job import JobQueue

class Brain(object):
    def __init__(self, config, sink=None):
        self.config = config
        self.sink = sink
        self.project_url = "https://github.com/adamwight/slander"
        if "irc" in self.config:
            if "ownermail" in self.config["irc"]:
                self.config["irc"]["ownermail"] = "xxx@example.com"
            if "regverify" in self.config["irc"]:
                self.config["irc"]["regverify"] = "*******"
        if "project_url" in self.config:
            self.project_url = self.config["project_url"]

    def say(self, message, force=False):
        if not force and 'mute' in self.config and int(self.config['mute']):
            print("muffling msg: " + message)
            return
        self.sink.say(self.sink.channel, message)

    def respond(self, user, message):
        if re.search(r'\bhelp\b', message):
            self.say("If I only had a brain: %s -- Commands: help config kill last" % (self.project_url, ))
        elif re.search(r'\bconfig\b', message):
            match = re.search(r'\b(?P<name>[^=\s]+)\s*=\s*(?P<value>\S+)', message)
            if match:
                self.config[match.group('name')] = match.group('value')

            dump = self.config
            dump['jobs'] = JobQueue.describe()
            dump = re.sub(r'p(ass)?w(ord)?[ :=]*[^ ]+', r'p***word', json.dumps(dump))
            self.say("Configuration: [%s]" % (dump, ), force=True)
        #elif re.search(r'\bkill\b', message):
        #    self.say("Squeal! Killed by %s" % (user, ))
        #    JobQueue.killall()
        #    #self.quit()
        #    #self.factory.stopTrying()
        elif re.search(r'\blast\b', message):
            if self.sink.timestamp:
                self.say("My last post was %s UTC" % (self.sink.timestamp, ))
            else:
                self.say("No activity.")
        else:
            print "Failed to handle incoming command: %s said %s" % (user, message)
