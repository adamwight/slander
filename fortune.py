import datetime
import os

class FortunePoller(object):
    def __init__(self, target=None, at_time=None):
        self.target = target
        self.at_time = at_time

        self.set_timer()

    def check(self):
        if self.time_arrived():
            self.set_timer()
            yield self.build_message()

    def time_arrived(self):
        now = datetime.datetime.now()
        return now >= self.timer

    def set_timer(self):
        today = datetime.date.today()
        time = datetime.datetime.strptime(self.at_time, "%H:%M").time()
        self.timer = datetime.datetime.combine(today, time)

        if self.time_arrived():
            # Add a day
            self.timer = self.timer + datetime.timedelta(1)

        print "Next timer is " + self.timer.isoformat()

    def build_message(self):
        # TODO: configurable message.
        cookie = os.popen("fortune").read()
        # TODO: 
        message = "{target}: {cookie} -- discuss.".format(
            target=self.target, cookie=cookie)
        return message
