"""Storage service interface."""
from abc import ABC, abstractmethod
from typing import BinaryIO


class IStorageService(ABC):
    """Storage service interface (domain)."""
    
    @abstractmethod
    async def upload(
        self,
        file_data: bytes,
        filename: str,
        folder: str = ""
    ) -> str:
        """
        Upload file and return URL.
        
        Args:
            file_data: File content as bytes
            filename: Name of the file
            folder: Optional folder path
            
        Returns:
            File URL or path
        """
        pass
    
    @abstractmethod
    async def download(self, file_url: str) -> bytes:
        """
        Download file.
        
        Args:
            file_url: File URL or path
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    async def delete(self, file_url: str) -> bool:
        """
        Delete file.
        
        Args:
            file_url: File URL or path
            
        Returns:
            True if deleted successfully
        """
        pass
