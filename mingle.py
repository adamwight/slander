import text
from feed import FeedPoller

import re

class MinglePoller(FeedPoller):
    """
    Format changes to Mingle cards
    """
    def parse(self, entry):
        m = re.search(r'^(.*/([0-9]+))', entry.id)
        url = m.group(1)
        issue = int(m.group(2))
        author = text.abbrevs(entry.author_detail.name)

        assignments = []
        details = entry.content[0].value
        assignment_phrases = [
            r'(?P<property>[^,>]+) set to (?P<value>[^,<]+\w)',
            r'(?P<property>[^,>]+) changed from (?P<previous_value>[^,<]+) to (?P<value>[^,<]+\w)',
        ]
        for pattern in assignment_phrases:
            for m in re.finditer(pattern, details):
                normal_form = None
                if re.match(r'\d{4}/\d{2}/\d{2}|\(not set\)', m.group('value')):
                    pass
                elif re.match(r'Planning - Sprint', m.group('property')):
                    n = re.search(r'(Sprint \d+)', m.group('value'))
                    normal_form = "->" + n.group(1)
                elif 'Deployed' == m.group('value'):
                    normal_form = "*Deployed*"
                else:
                    normal_form = text.abbrevs(m.group('property')+" : "+m.group('value'))

                if normal_form:
                    assignments.append(normal_form)
        summary = '|'.join(assignments)

        for m in re.finditer(r'(?P<property>[^:>]+): (?P<value>[^<]+)', details):
            if m.group('property') == 'Comment added':
                summary = m.group('value')+" "+summary
        for m in re.finditer(r'Description changed', details):
            summary += " " + m.group(0)

        summary = text.trunc(summary)

        if summary:
            return "#%d: (%s) %s -- %s" % (issue, author, summary, url)
