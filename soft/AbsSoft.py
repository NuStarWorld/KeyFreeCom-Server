from abc import ABC, abstractmethod

class AbsSoft(ABC):
    @abstractmethod
    def run(self,**kwargs):
        pass