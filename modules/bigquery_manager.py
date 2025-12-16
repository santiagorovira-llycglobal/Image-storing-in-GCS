"""
BigQuery Manager Module
Handles all BigQuery operations including table creation and URL uploads.
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd


class BigQueryManager:
    """Manages BigQuery operations for storing image URLs."""
    
    def __init__(self, config):
        """
        Initialize the BigQuery Manager.
        
        Args:
            config: Config object with BigQuery settings
        """
        self.config = config
        
        # Initialize BigQuery client
        creds = Credentials.from_service_account_file(
            config.service_account_file
        )
        self.client = bigquery.Client(
            credentials=creds,
            project=config.bq_project_id
        )
        
        self.table_id = config.get_bq_table_id()
    
    def create_table_if_not_exists(self):
        """
        Create the BigQuery table if it doesn't exist.
        
        Schema:
        - original_url: STRING - The original image URL from the sheet
        - gcs_url: STRING - The GCS storage URL
        - filename: STRING - The filename in GCS
        - upload_timestamp: TIMESTAMP - When the image was uploaded
        - row_index: INTEGER - The row index from the sheet
        """
        schema = [
            bigquery.SchemaField("original_url", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("gcs_url", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("filename", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("upload_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("row_index", "INTEGER", mode="REQUIRED"),
        ]
        
        table = bigquery.Table(self.table_id, schema=schema)
        
        try:
            # Try to get the table
            self.client.get_table(self.table_id)
            print(f"Table {self.table_id} already exists.")
        except Exception:
            # Table doesn't exist, create it
            table = self.client.create_table(table)
            print(f"Created table {self.table_id}")
    
    def upload_urls(self, records):
        """
        Upload image URL records to BigQuery.
        
        Args:
            records: List of dictionaries with keys:
                - original_url
                - gcs_url
                - filename
                - upload_timestamp
                - row_index
                
        Returns:
            dict: Result with 'success' boolean and 'rows_inserted' count or 'error'
        """
        if not records:
            return {
                'success': True,
                'rows_inserted': 0
            }
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # Ensure upload_timestamp is datetime
            if 'upload_timestamp' not in df.columns:
                df['upload_timestamp'] = datetime.utcnow()
            
            # Configure load job
            job_config = bigquery.LoadJobConfig(
                write_disposition=self.config.bq_write_disposition,
                schema=[
                    bigquery.SchemaField("original_url", "STRING"),
                    bigquery.SchemaField("gcs_url", "STRING"),
                    bigquery.SchemaField("filename", "STRING"),
                    bigquery.SchemaField("upload_timestamp", "TIMESTAMP"),
                    bigquery.SchemaField("row_index", "INTEGER"),
                ]
            )
            
            # Load data
            job = self.client.load_table_from_dataframe(
                df, 
                self.table_id, 
                job_config=job_config
            )
            
            # Wait for the job to complete
            job.result()
            
            return {
                'success': True,
                'rows_inserted': len(records)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"BigQuery upload error: {str(e)}"
            }
    
    def get_table_info(self):
        """
        Get information about the BigQuery table.
        
        Returns:
            dict: Table information including row count
        """
        try:
            table = self.client.get_table(self.table_id)
            return {
                'exists': True,
                'num_rows': table.num_rows,
                'created': table.created,
                'modified': table.modified
            }
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }
