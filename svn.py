import text

from xml.etree.cElementTree import parse as xmlparse
from cStringIO import StringIO
from subprocess import Popen, PIPE

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
        comment = text.strip(tree.find(".//msg").text, truncate=True)
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
