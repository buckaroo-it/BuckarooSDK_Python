from abc import ABC, abstractmethod
from .subject_interface import SubjectInterface
from typing import Optional


class Loggable(ABC):
    @property
    @abstractmethod
    def logger(self) -> Optional[SubjectInterface]:
        pass

    @logger.setter
    @abstractmethod
    def logger(self, logger: SubjectInterface) -> None:
        pass
