"""
Configuration Management Module
Loads and validates all environment variables for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager for the image storage system."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Google Sheets Configuration
        self.spreadsheet_key = os.getenv('SPREADSHEET_KEY')
        self.worksheet_name = os.getenv('WORKSHEET_NAME')
        self.url_column_name = os.getenv('URL_COLUMN_NAME')
        
        # Google Cloud Storage Configuration
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')
        self.gcs_folder_path = os.getenv('GCS_FOLDER_PATH', '')
        
        # BigQuery Configuration
        self.bq_project_id = os.getenv('BQ_PROJECT_ID')
        self.bq_dataset = os.getenv('BQ_DATASET')
        self.bq_table_name = os.getenv('BQ_TABLE_NAME')
        self.bq_write_disposition = os.getenv('BQ_WRITE_DISPOSITION', 'WRITE_APPEND')
        
        # Authentication
        self.service_account_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Validate critical configuration
        self._validate()
    
    def _validate(self):
        """Validate that all critical configuration values are present."""
        required_fields = {
            'SPREADSHEET_KEY': self.spreadsheet_key,
            'URL_COLUMN_NAME': self.url_column_name,
            'GCS_BUCKET_NAME': self.gcs_bucket_name,
            'BQ_PROJECT_ID': self.bq_project_id,
            'BQ_DATASET': self.bq_dataset,
            'BQ_TABLE_NAME': self.bq_table_name,
            'GOOGLE_APPLICATION_CREDENTIALS': self.service_account_file
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    def get_gcs_blob_path(self, filename):
        """
        Get the full GCS blob path for a filename.
        
        Args:
            filename: The filename to store
            
        Returns:
            Full blob path including folder if configured
        """
        if self.gcs_folder_path:
            # Ensure folder path ends with /
            folder = self.gcs_folder_path if self.gcs_folder_path.endswith('/') else f"{self.gcs_folder_path}/"
            return f"{folder}{filename}"
        return filename
    
    def get_bq_table_id(self):
        """
        Get the full BigQuery table ID.
        
        Returns:
            Full table ID in format: project.dataset.table
        """
        return f"{self.bq_project_id}.{self.bq_dataset}.{self.bq_table_name}"
