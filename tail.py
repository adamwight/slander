class TailPoller(object):
    """Tail -f a file as the message source"""

    def __init__(self, path=None):
        print "Initializing file tailer on: [{path}]".format(path=path)

        self.path = path
        self.file = file(path, "r")

    def check(self):
        data = self.file.readline().strip()

        if data:
            yield data
