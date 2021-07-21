from abc import ABC, abstractmethod
import logging


class AbstractLogger(ABC):
    @abstractmethod
    def info(self, msg):
        pass

    @abstractmethod
    def error(self, msg):
        pass

    @abstractmethod
    def debug(self, msg):
        pass

    @abstractmethod
    def warn(self, msg):
        pass

    @abstractmethod
    def exception(self, msg):
        pass


class Logginglogger(AbstractLogger):
    def __init__(self, format="[%(asctime)s][%(levelname)s]: %(message)s", **kwargs):
        logging.basicConfig(
            format=format,
            level=logging.INFO if not kwargs.get("debug") else logging.DEBUG,
        )

    def info(self, msg):
        return logging.info(msg)

    def error(self, msg):
        return logging.error(msg)

    def debug(self, msg):
        return logging.debug(msg)

    def warn(self, msg):
        return logging.warning(msg)

    def exception(self, msg):
        return logging.exception(msg)


Logger = Logginglogger()