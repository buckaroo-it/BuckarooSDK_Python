from abc import ABC, abstractmethod


class ReplyStrategyInterface(ABC):

    @abstractmethod
    def validate(self) -> bool:
        pass
