from abc import ABC,abstractmethod

class Server(ABC):
    @abstractmethod
    def receive_msg(self,*args):
        pass

    @abstractmethod
    def send_msg(self,*args):
        pass