import datetime

#pip install twisted twisted.words
from twisted.words.protocols import irc
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

import text
from job import JobQueue
from brain import Brain

class RelayToIRC(irc.IRCClient):
    """
    Bot brain will spawn listening jobs and then relay results to an irc channel.
    """
    timestamp = None

    def connectionMade(self):
        self.config = self.factory.config
        self.nickname = self.config["irc"]["nick"]
        self.realname = self.config["irc"]["realname"]
        self.channel = self.config["irc"]["channel"]
        if "maxlen" in self.config["irc"]:
            text.maxlen = self.config["irc"]["maxlen"]

        irc.IRCClient.connectionMade(self)

        if "pass" in self.config["irc"]:
            self.msg("NickServ", "IDENTIFY %s" % self.config["irc"]["pass"])

    def signedOn(self):
        self.join(self.channel)

    def joined(self, channel):
        print "Joined channel %s as %s" % (channel, self.nickname)
        self.brain = Brain(self.config, sink=self)
        #XXX get outta here:
        source = JobQueue(
            definition=self.config["jobs"],
            sink=self,
            interval=self.config["poll_interval"]
        )
        source.run()

    def privmsg(self, user, channel, message):
        if message.find(self.nickname) >= 0:
            self.brain.respond(user, message)

    def write(self, data):
        if isinstance(data, list):
            for line in data:
                self.write(line)
            return
        self.say(self.channel, data.encode('ascii', 'replace'))
        self.timestamp = datetime.datetime.utcnow()


    @staticmethod
    def run(config):
        factory = ReconnectingClientFactory()
        factory.protocol = RelayToIRC
        factory.config = config
        reactor.connectTCP(config["irc"]["host"], config["irc"]["port"], factory)
        reactor.run()
