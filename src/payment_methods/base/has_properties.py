from abc import ABC, abstractmethod

from src.transaction import Client, TransactionRequest

class HasClient(ABC):

    @property
    @abstractmethod
    def client(self) -> Client: pass    

class HasPayload(ABC):
    
    @property
    @abstractmethod
    def payload(self) -> dict: pass

class HasTransationRequest(ABC):   

    @property
    @abstractmethod
    def transaction_request(self) -> TransactionRequest: pass
