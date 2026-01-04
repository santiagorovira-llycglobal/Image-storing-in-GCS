import os
from google.cloud import storage

class GCSUtils:
    def __init__(self, bucket_name=None):
        self.client = storage.Client()
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is not set.")
        self.bucket = self.client.bucket(self.bucket_name)
        self.folder_path = os.getenv("GCS_FOLDER_PATH", "").strip("/")

    def upload_to_gcs(self, content, filename, content_type="image/jpeg"):
        """
        Uploads bytes to GCS and returns the public URL.
        """
        blob_name = filename
        if self.folder_path:
            blob_name = f"{self.folder_path}/{filename}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=content_type)
        
        # Make the blob public for Looker Studio access
        try:
            blob.make_public()
        except Exception as e:
            print(f"Warning: Could not make blob public due to bucket settings: {e}")
            print("To fix this, enable public access at the bucket level by granting 'Storage Object Viewer' to 'allUsers'.")
        
        return blob.public_url

    def get_public_url(self, blob_name):
        """
        Returns the public URL for a given blob name.
        """
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
