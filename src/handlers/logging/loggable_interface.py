from abc import ABC, abstractmethod
from typing import Optional

import src.handlers.logging.subject_interface as subject_interface


class Loggable(ABC):
    @property
    @abstractmethod
    def logger(self) -> Optional[subject_interface.SubjectInterface]:
        pass

    @logger.setter
    @abstractmethod
    def logger(self, logger: subject_interface.SubjectInterface) -> None:
        pass
