"""
Object Storage Manager - MinIO Integration

Handles file storage for agents, tools, and knowledge base documents.
"""

import asyncio
import io
from typing import Optional, BinaryIO
from datetime import timedelta

from minio import Minio
from minio.error import S3Error
from ..core.config import settings


class StorageManager:
    """Manages object storage using MinIO"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = settings.minio_bucket_name
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.use_ssl = settings.minio_use_ssl
        
    async def initialize(self):
        """Initialize MinIO client and ensure bucket exists"""
        # Create MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.use_ssl
        )
        
        # Create bucket if it doesn't exist
        await self._ensure_bucket_exists()
        
        print(f"✅ MinIO storage initialized (bucket: {self.bucket_name})")
    
    async def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if not"""
        try:
            # Check if bucket exists
            bucket_exists = await asyncio.to_thread(
                self.client.bucket_exists,
                self.bucket_name
            )
            
            if not bucket_exists:
                # Create bucket
                await asyncio.to_thread(
                    self.client.make_bucket,
                    self.bucket_name
                )
                print(f"✅ Created MinIO bucket: {self.bucket_name}")
            
        except S3Error as e:
            print(f"❌ Error ensuring bucket exists: {str(e)}")
            raise
    
    async def upload_file(
        self,
        object_name: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict = None
    ) -> str:
        """
        Upload a file to MinIO
        
        Args:
            object_name: Name/path of the object in the bucket
            file_data: File content as bytes
            content_type: MIME type of the file
            metadata: Optional metadata dictionary
            
        Returns:
            Object name (key) in the bucket
        """
        try:
            # Convert bytes to file-like object
            file_stream = io.BytesIO(file_data)
            file_size = len(file_data)
            
            # Upload to MinIO
            await asyncio.to_thread(
                self.client.put_object,
                self.bucket_name,
                object_name,
                file_stream,
                file_size,
                content_type=content_type,
                metadata=metadata or {}
            )
            
            return object_name
            
        except S3Error as e:
            print(f"❌ Error uploading file {object_name}: {str(e)}")
            raise
    
    async def upload_text(
        self,
        object_name: str,
        text_content: str,
        content_type: str = "text/plain",
        metadata: dict = None
    ) -> str:
        """Upload text content to MinIO"""
        file_data = text_content.encode('utf-8')
        return await self.upload_file(object_name, file_data, content_type, metadata)
    
    async def download_file(self, object_name: str) -> bytes:
        """
        Download a file from MinIO
        
        Args:
            object_name: Name/path of the object in the bucket
            
        Returns:
            File content as bytes
        """
        try:
            # Download from MinIO
            response = await asyncio.to_thread(
                self.client.get_object,
                self.bucket_name,
                object_name
            )
            
            # Read all data
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            print(f"❌ Error downloading file {object_name}: {str(e)}")
            raise
    
    async def download_text(self, object_name: str) -> str:
        """Download text content from MinIO"""
        data = await self.download_file(object_name)
        return data.decode('utf-8')
    
    async def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from MinIO
        
        Args:
            object_name: Name/path of the object to delete
            
        Returns:
            True if successful
        """
        try:
            await asyncio.to_thread(
                self.client.remove_object,
                self.bucket_name,
                object_name
            )
            return True
            
        except S3Error as e:
            print(f"❌ Error deleting file {object_name}: {str(e)}")
            return False
    
    async def list_files(self, prefix: str = "") -> list:
        """
        List files in the bucket with optional prefix
        
        Args:
            prefix: Optional prefix to filter objects
            
        Returns:
            List of object names
        """
        try:
            objects = await asyncio.to_thread(
                self.client.list_objects,
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            print(f"❌ Error listing files: {str(e)}")
            return []
    
    async def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a presigned URL for temporary access to an object
        
        Args:
            object_name: Name/path of the object
            expires: How long the URL should be valid
            
        Returns:
            Presigned URL
        """
        try:
            url = await asyncio.to_thread(
                self.client.presigned_get_object,
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
            
        except S3Error as e:
            print(f"❌ Error generating presigned URL: {str(e)}")
            raise
    
    async def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO"""
        try:
            await asyncio.to_thread(
                self.client.stat_object,
                self.bucket_name,
                object_name
            )
            return True
        except S3Error:
            return False
    
    async def get_file_info(self, object_name: str) -> dict:
        """Get metadata about a file"""
        try:
            stat = await asyncio.to_thread(
                self.client.stat_object,
                self.bucket_name,
                object_name
            )
            
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata
            }
            
        except S3Error as e:
            print(f"❌ Error getting file info: {str(e)}")
            return {}
    
    async def copy_file(self, source_name: str, dest_name: str) -> bool:
        """Copy a file within the bucket"""
        try:
            from minio.commonconfig import CopySource
            
            await asyncio.to_thread(
                self.client.copy_object,
                self.bucket_name,
                dest_name,
                CopySource(self.bucket_name, source_name)
            )
            return True
            
        except S3Error as e:
            print(f"❌ Error copying file: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up resources"""
        # MinIO client doesn't need explicit cleanup
        pass


# Global storage manager instance
storage_manager = StorageManager()


# Helper functions for common operations
async def save_agent_code(agent_id: str, code: str) -> str:
    """Save agent code to storage"""
    object_name = f"agents/{agent_id}/code.py"
    await storage_manager.upload_text(object_name, code, "text/x-python")
    return object_name


async def save_tool_code(tool_id: str, code: str) -> str:
    """Save tool code to storage"""
    object_name = f"tools/{tool_id}/code.py"
    await storage_manager.upload_text(object_name, code, "text/x-python")
    return object_name


async def save_knowledge_document(project_id: str, filename: str, content: bytes) -> str:
    """Save knowledge base document to storage"""
    object_name = f"knowledge/{project_id}/{filename}"
    content_type = _get_content_type(filename)
    await storage_manager.upload_file(object_name, content, content_type)
    return object_name


async def save_task_result(task_id: str, result_data: str) -> str:
    """Save task execution result to storage"""
    object_name = f"results/{task_id}/result.json"
    await storage_manager.upload_text(object_name, result_data, "application/json")
    return object_name


def _get_content_type(filename: str) -> str:
    """Determine content type from filename"""
    extension = filename.lower().split('.')[-1]
    
    content_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'csv': 'text/csv',
        'json': 'application/json',
        'py': 'text/x-python',
        'js': 'text/javascript',
        'ts': 'text/typescript',
        'html': 'text/html',
        'css': 'text/css',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'svg': 'image/svg+xml'
    }
    
    return content_types.get(extension, 'application/octet-stream')
