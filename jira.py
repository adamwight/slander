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
        if 'content' in entry:
            details = entry.content[0].value
            assignment_phrases = [
                r"Changed the (?P<property>[^']+) to '(?P<value>[^']+)'",
                r"Added the (?P<property>[^']+) '(?P<value>[^']+)'",
                r"Removed the (?P<property>[^']+) '(?P<previous_value>[^']+)'",
            ]
            assignments = dict()
            to_strip = []
            for pattern in assignment_phrases:
                for m in re.finditer(pattern, details):
                    #if 'previous_value' in m.groupdict():
                    #    normal_form = "%s:%s->%s" % (text.abbrevs(m.group('property')), m.group("previous_value"), m.group('value'))
                    #else:
                    if 'value' in m.groupdict():
                        assignments[text.abbrevs(m.group('property'))] = m.group('value')

                    to_strip.append(m.group(0))

            revs = set()
            for m in re.finditer(r'r=(\d+)', details):
                revs.add(", r"+m.group(1))

            normal_form_assignments = "|".join(["%s:%s" % (k, v) for k, v in assignments.items()])
            for p in to_strip:
                details = details.replace(p, "")

            summary = "%s %s %s" % (normal_form_assignments, "".join(revs), details)

        else:
            summary = entry.summary
        summary = text.strip(summary, truncate=True)
        url = "%s/browse/%s" % (self.base_url, issue)

        return "%s: %s %s -- %s" % (entry.usr_username, issue, summary, url)
