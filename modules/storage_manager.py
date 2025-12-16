"""
Google Cloud Storage Manager Module
Handles all GCS operations including duplicate checking and image uploads.
"""

import requests
from google.cloud import storage
from google.oauth2.service_account import Credentials


class StorageManager:
    """Manages Google Cloud Storage operations for image storage."""
    
    def __init__(self, config):
        """
        Initialize the Storage Manager.
        
        Args:
            config: Config object with GCS settings
        """
        self.config = config
        
        # Initialize GCS client
        scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/devstorage.full_control"
        ]
        creds = Credentials.from_service_account_file(
            config.service_account_file, 
            scopes=scopes
        )
        self.storage_client = storage.Client(credentials=creds)
        self.bucket = self.storage_client.bucket(config.gcs_bucket_name)
    
    def check_image_exists(self, blob_path):
        """
        Check if an image already exists in GCS.
        
        Args:
            blob_path: The full path to the blob in GCS
            
        Returns:
            True if the image exists, False otherwise
        """
        blob = self.bucket.blob(blob_path)
        return blob.exists()
    
    def upload_image(self, url, blob_path, timeout=10):
        """
        Download an image from a URL and upload it to GCS.
        
        Args:
            url: The URL of the image to download
            blob_path: The destination path in GCS
            timeout: Request timeout in seconds
            
        Returns:
            dict: Result with 'success' boolean, 'gcs_url' if successful, 'error' if failed
        """
        try:
            # Download the image
            response = requests.get(url, stream=True, timeout=timeout)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code} when downloading image"
                }
            
            # Upload to GCS
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                response.content,
                content_type=response.headers.get('Content-Type', 'image/jpeg')
            )
            
            # Get the public URL
            gcs_url = self.get_public_url(blob_path)
            
            return {
                'success': True,
                'gcs_url': gcs_url,
                'blob_path': blob_path
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Request error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Upload error: {str(e)}"
            }
    
    def get_public_url(self, blob_path):
        """
        Get the public URL for a blob in GCS.
        
        Args:
            blob_path: The path to the blob in GCS
            
        Returns:
            The public URL as a string
        """
        return f"gs://{self.config.gcs_bucket_name}/{blob_path}"
    
    def list_existing_images(self):
        """
        List all images in the configured GCS bucket/folder.
        
        Returns:
            List of blob names
        """
        prefix = self.config.gcs_folder_path if self.config.gcs_folder_path else None
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    
    @staticmethod
    def get_filename_from_url(url, index):
        """
        Generate a safe filename from a URL and index.
        
        Args:
            url: The source URL
            index: Row index for uniqueness
            
        Returns:
            A safe filename string
        """
        try:
            # Extract the original filename from URL
            original_name = url.split("/")[-1].split("?")[0]
            if not original_name:
                original_name = "imagen_sin_nombre.jpg"
        except:
            original_name = "error_nombre.jpg"
        
        # Return format: 001_filename.jpg
        return f"{str(index).zfill(3)}_{original_name}"
