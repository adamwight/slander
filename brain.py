import re
import json

from job import JobQueue

class Brain(object):
    def __init__(self, config, sink=None):
        self.config = config
        self.sink = sink
        if "irc" in self.config:
            if "ownermail" in self.config["irc"]:
                self.config["irc"]["ownermail"] = "xxx@example.com"
            if "regverify" in self.config["irc"]:
                self.config["irc"]["regverify"] = "*******"

        self.source_url = self.config["source_url"]

    def say(self, message, force=False):
        if not force and 'mute' in self.config and int(self.config['mute']):
            print("muffling msg: " + message)
            return
        self.sink.say(self.sink.channel, message)

    def respond(self, user, message):
        if re.search(r'\bhelp\b', message):
            self.say("If I only had a brain: %s -- Commands: help config kill last" % (self.source_url, ))
        elif re.search(r'\bconfig\b', message):
            match = re.search(r'\b(?P<name>[^=\s]+)\s*=\s*(?P<value>\S+)', message)
            if match:
                self.config[match.group('name')] = match.group('value')

            dump = self.config
            dump['jobs'] = JobQueue.describe()
            dumpstr = json.dumps(self.redact(dump))
            self.say("Configuration: [{dump}]".format(dump=dumpstr), force=True)
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

    def redact(self, data):
        FORBIDDEN_KEY_PATTERN = r'pw|pass|password'
        BLACKOUT = "p***word"

        for key, value in data.items():
            if re.match(FORBIDDEN_KEY_PATTERN, key):
                data[key] = BLACKOUT
            elif hasattr(value, 'items'):
                data[key] = self.redact(value)

        return data
