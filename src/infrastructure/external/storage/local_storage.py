"""Local file storage implementation."""
import os
import aiofiles
from pathlib import Path
from src.domain.interfaces.storage_service import IStorageService
from src.config import settings


class LocalStorageService(IStorageService):
    """Local file system storage."""
    
    def __init__(self, base_path: str = None):
        """Initialize local storage."""
        self.upload_dir = Path(base_path or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload(
        self,
        file_data: bytes,
        filename: str,
        folder: str = ""
    ) -> str:
        """
        Save file locally.
        
        Args:
            file_data: File content as bytes
            filename: Name of the file
            folder: Optional folder path
            
        Returns:
            Relative path as URL
        """
        # Create folder path
        folder_path = self.upload_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Full file path
        file_path = folder_path / filename
        
        # Write file async
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        # Return relative path as URL
        return str(file_path.relative_to(self.upload_dir))
    
    async def download(self, file_url: str) -> bytes:
        """
        Read file.
        
        Args:
            file_url: Relative file path
            
        Returns:
            File content as bytes
        """
        file_path = self.upload_dir / file_url
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_url}")
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def delete(self, file_url: str) -> bool:
        """
        Delete file.
        
        Args:
            file_url: Relative file path
            
        Returns:
            True if deleted successfully
        """
        file_path = self.upload_dir / file_url
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
