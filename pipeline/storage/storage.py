from __future__ import annotations

from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    @abstractmethod
    def put_bytes(self, *, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def get_bytes(self, *, key: str) -> bytes:
        raise NotImplementedError
    
    @abstractmethod
    def upload_file(self, *, local_path: str, key: str, content_type: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def download_file(self, *, key: str, local_path: str) -> None:
        raise NotImplementedError