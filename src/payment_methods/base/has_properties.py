from abc import ABC, abstractmethod

import src.transaction.client as client
import src.transaction.request.transaction_request as transaction_request


class HasClient(ABC):

    @property
    @abstractmethod
    def client(self) -> client.Client:
        pass


class HasPayload(ABC):

    @property
    @abstractmethod
    def payload(self) -> dict:
        pass


class HasTransationRequest(ABC):

    @property
    @abstractmethod
    def transaction_request(self) -> transaction_request.TransactionRequest:
        pass
