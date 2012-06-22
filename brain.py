import re

from job import JobQueue

class Brain(object):
    def __init__(self, config, sink=None):
        self.config = config
        self.sink = sink
        self.project_url = "https://github.com/adamwight/slander"
        if "project_url" in self.config:
            self.project_url = self.config["project_url"]

    def say(self, message):
        self.sink.say(self.sink.channel, message)

    def respond(self, user, message):
        if re.search(r'\bhelp\b', message):
            self.say("If I only had a brain: %s -- Commands: help jobs kill last" % (self.project_url, ))
        elif re.search(r'\bjobs\b', message):
            jobs_desc = JobQueue.describe()
            jobs_desc = re.sub(r'p(ass)?w(ord)?[ :=]*[^ ]+', r'p***word', jobs_desc)

            self.say("Running jobs [%s]" % (jobs_desc, ))
        #elif re.search(r'\bkill\b', message):
        #    self.say("Squeal! Killed by %s" % (user, ))
        #    self.factory.stopTrying()
        #    self.quit()
        elif re.search(r'\blast\b', message):
            if self.sink.timestamp:
                self.say("My last post was %s UTC" % (self.sink.timestamp, ))
            else:
                self.say("No activity.")
        else:
            print "Failed to handle incoming command: %s said %s" % (user, message)
