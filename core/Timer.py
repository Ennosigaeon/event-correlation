import atexitimport loggingimport timeclass Timer:    def __init__(self):        self.startTime = None        self.difference = None    def start(self):        self.startTime = time.perf_counter()        atexit.register(self.stopAndLog, abort=True)    def stop(self):        if (self.difference is None):            self.difference = time.perf_counter() - self.startTime            # round to millisecond            self.difference = int(self.difference * 1000)    def stopAndLog(self, abort=False):        if (abort and self.difference is not None):            return        self.stop()        if (abort):            logging.warning("Calculation aborted after {}".format(Timer.millisToStr(self.difference)))        return str(self)    def __str__(self):        if (self.startTime is not None):            if (self.difference is None):                return "Timer started {} ago".format(Timer.millisToStr(time.perf_counter() - self.startTime))            else:                return Timer.millisToStr(self.difference)        return "Timer instance"    @staticmethod    def millisToStr(milliSeconds):        if (isinstance(milliSeconds, float)):            milliSeconds = int(milliSeconds * 1000)        s, milli = divmod(milliSeconds, 1000)        m, s = divmod(s, 60)        return "{:02d}:{:02d},{:03d}".format(m, s, milli)