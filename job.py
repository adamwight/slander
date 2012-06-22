from twisted.internet.task import LoopingCall

jobs = []

class JobQueue(object):
    def __init__(self, definition, sink, interval):
        """
        Read job definitions from a config source, create an instance of the job using its configuration, and store the config for reference.
        """
        self.sink = sink
        self.interval = interval
        for type_name, options in definition.items():
            classname = type_name.capitalize() + "Poller"
            m = __import__(type_name, fromlist=[classname])
            if hasattr(m, classname):
                klass = getattr(m, classname)
                job = klass(**options)
                job.config = options
                job.config['class'] = type_name
                jobs.append(job)
            else:
                raise Exception("Failed to create job of type " + classname)

    @staticmethod
    def describe():
        jobs_desc = ", ".join(
            [("%s: %s" % (j.config['class'], j.config))
                for j in jobs]
        )
        return jobs_desc

    def check(self):
        for job in jobs:
            for line in job.check():
                if line:
                    self.sink.write(line)

    def run(self):
        task = LoopingCall(self.check)
        task.start(self.interval)
        print "Started polling jobs, every %d seconds." % (self.interval, )
