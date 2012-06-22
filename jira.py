import text
from feed import FeedPoller

import re

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
        summary = text.strip(entry.summary, truncate=True)
        url = "%s/browse/%s" % (self.base_url, issue)

        return "%s: %s %s -- %s" % (entry.author_detail.name, issue, summary, url)
