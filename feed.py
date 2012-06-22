import feedparser
from HTMLParser import HTMLParser

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
