import feedparser

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
        skipping = True
        for entry in result.entries:
            if (self.last_seen_id == entry.id):
                skipping = False
            elif not skipping:
                yield self.parse(entry)

        if result.entries:
            self.last_seen_id = result.entries[-1].id

    def parse(self, entry):
        return "%s [%s]" % (entry.summary, entry.link)
