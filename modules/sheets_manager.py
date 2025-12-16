"""
Google Sheets Manager Module
Handles all Google Sheets operations for reading image URLs.
"""

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials


class SheetsManager:
    """Manages Google Sheets operations for reading image data."""
    
    def __init__(self, config):
        """
        Initialize the Sheets Manager.
        
        Args:
            config: Config object with Sheets settings
        """
        self.config = config
        
        # Initialize Sheets client
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            config.service_account_file,
            scopes=scopes
        )
        self.client = gspread.authorize(creds)
    
    def read_sheet_data(self):
        """
        Read data from the configured Google Sheet.
        
        Returns:
            pandas.DataFrame: The sheet data as a DataFrame
            
        Raises:
            Exception: If the sheet cannot be read or the URL column doesn't exist
        """
        try:
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(self.config.spreadsheet_key)
            
            # Get the worksheet
            if self.config.worksheet_name:
                worksheet = spreadsheet.worksheet(self.config.worksheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            # Get all records as a list of dictionaries
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Validate that the URL column exists
            if self.config.url_column_name not in df.columns:
                raise ValueError(
                    f"Column '{self.config.url_column_name}' not found in sheet. "
                    f"Available columns: {', '.join(df.columns)}"
                )
            
            return df
            
        except Exception as e:
            raise Exception(f"Error reading Google Sheets: {str(e)}")
    
    def update_sheet_with_gcs_urls(self, row_updates):
        """
        Update the Google Sheet with GCS URLs (optional feature).
        
        Args:
            row_updates: List of tuples (row_index, gcs_url)
            
        Returns:
            dict: Result with 'success' boolean and 'rows_updated' count or 'error'
        """
        try:
            # Open the spreadsheet
            spreadsheet = self.client.open_by_key(self.config.spreadsheet_key)
            
            if self.config.worksheet_name:
                worksheet = spreadsheet.worksheet(self.config.worksheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            # Find or create a column for GCS URLs
            headers = worksheet.row_values(1)
            
            if 'GCS_URL' not in headers:
                # Add new column header
                gcs_col_index = len(headers) + 1
                worksheet.update_cell(1, gcs_col_index, 'GCS_URL')
            else:
                gcs_col_index = headers.index('GCS_URL') + 1
            
            # Update cells
            for row_index, gcs_url in row_updates:
                # row_index is 0-based from DataFrame, sheet is 1-based + 1 for header
                sheet_row = row_index + 2
                worksheet.update_cell(sheet_row, gcs_col_index, gcs_url)
            
            return {
                'success': True,
                'rows_updated': len(row_updates)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Sheet update error: {str(e)}"
            }
