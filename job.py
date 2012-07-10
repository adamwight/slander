from twisted.internet.task import LoopingCall
import copy

class JobQueue(object):
    threads = []
    jobs_def = []

    def __init__(self, definition, sink, interval):
        """
        Read job definitions from a config source, create an instance of the job using its configuration, and store the config for reference.
        """
        self.sink = sink
        self.interval = interval
        JobQueue.jobs_def = []
        for type_name, options in definition.items():
            classname = type_name.capitalize() + "Poller"
            m = __import__(type_name, fromlist=[classname])
            if hasattr(m, classname):
                klass = getattr(m, classname)
                job = klass(**options)
                job.config = copy.deepcopy(options)
                job.config['class'] = type_name
                JobQueue.jobs_def.append(job)
            else:
                raise Exception("Failed to create job of type " + classname)

    @staticmethod
    def describe():
        jobs_desc = ", ".join(
            [("%s: %s" % (j.config['class'], j.config))
                for j in JobQueue.jobs_def]
        )
        return jobs_desc

    def check(self):
        for job in JobQueue.jobs_def:
            for line in job.check():
                if line:
                    self.sink.write(line)

    @staticmethod
    def killall():
        for old in JobQueue.threads:
            old.stop()
        JobQueue.threads = []

    def run(self):
        JobQueue.killall()
        task = LoopingCall(self.check)
        JobQueue.threads = [task]
        task.start(self.interval)
        print "Started polling jobs, every %d seconds." % (self.interval, )
