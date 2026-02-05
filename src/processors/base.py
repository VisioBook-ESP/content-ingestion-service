from abc import ABC, abstractmethod


class BaseProcessor(ABC):
    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        ...

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        ...

    @abstractmethod
    def extract_metadata(self, file_path: str) -> dict:
        ...
