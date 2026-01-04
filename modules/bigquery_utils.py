from google.cloud import bigquery
from google.oauth2 import service_account
import os

class BigQueryUtils:
    def __init__(self):
        self.source_table = os.getenv("BQ_SOURCE_TABLE")
        self.storage_table = os.getenv("BQ_STORAGE_TABLE")
        
        if not self.source_table or not self.storage_table:
            raise ValueError("BQ_SOURCE_TABLE and BQ_STORAGE_TABLE environment variables must be set.")

        # Load credentials with Drive scopes for external tables
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and os.path.exists(credentials_path):
            scopes = [
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/cloud-platform",
            ]
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
            self.client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        else:
            # Fallback to default credentials (e.g. in GCF environment)
            self.client = bigquery.Client()

    def _ensure_storage_table_exists(self):
        """
        Checks if the storage table exists, and creates it if it doesn't.
        Also ensures the ImageID column exists.
        """
        try:
            table = self.client.get_table(self.storage_table)
            schema = table.schema
            if not any(field.name == 'ImageID' for field in schema):
                print(f"Adding ImageID column to {self.storage_table}...")
                new_schema = list(schema)
                new_schema.append(bigquery.SchemaField("ImageID", "STRING", mode="NULLABLE"))
                table.schema = new_schema
                self.client.update_table(table, ["schema"])
        except Exception as e:
            if "Not found" in str(e):
                print(f"Creating storage table: {self.storage_table}")
                schema = [
                    bigquery.SchemaField("OriginalURL", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("GCSURL", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("ImageID", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("ProcessedAt", "TIMESTAMP", default_value_expression="CURRENT_TIMESTAMP"),
                ]
                table = bigquery.Table(self.storage_table, schema=schema)
                self.client.create_table(table)
            else:
                raise e

    def get_processed_image_ids(self):
        """
        Fetches all processed ImageIDs from the storage table.
        """
        query = f"SELECT ImageID FROM `{self.storage_table}` WHERE ImageID IS NOT NULL"
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return set(row.ImageID for row in results)
        except Exception:
            return set()

    def get_unprocessed_urls(self):
        """
        Queries BigQuery for URLs in the source table that are not in the storage table.
        """
        query = f"""
            SELECT src.AdURL
            FROM `{self.source_table}` AS src
            LEFT JOIN `{self.storage_table}` AS stg
            ON src.AdURL = stg.OriginalURL
            WHERE stg.OriginalURL IS NULL
        """
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [row.AdURL for row in results]
        except Exception as e:
            if "Not found" in str(e) and self.storage_table in str(e):
                print("Storage table not found, attempting to get all URLs from source.")
                return self._get_all_source_urls()
            print(f"Error querying BigQuery: {e}")
            return []

    def _get_all_source_urls(self):
        """Helper to get all URLs from the source table."""
        query = f"SELECT AdURL FROM `{self.source_table}`"
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [row.AdURL for row in results]
        except Exception as e:
            print(f"Error querying source table: {e}")
            return []

    def record_processed_url(self, original_url, gcs_url, image_id):
        """
        Inserts a record into the storage table.
        """
        # Ensure table exists before inserting
        try:
            self._ensure_storage_table_exists()
        except Exception as e:
            print(f"Could not ensure storage table exists: {e}")
            return False

        rows_to_insert = [
            {"OriginalURL": original_url, "GCSURL": gcs_url, "ImageID": image_id}
        ]
        try:
            errors = self.client.insert_rows_json(self.storage_table, rows_to_insert)
            if errors == []:
                print(f"Successfully recorded: {original_url}")
                return True
            else:
                print(f"Errors inserting rows: {errors}")
                return False
        except Exception as e:
            print(f"Error inserting into BigQuery: {e}")
            return False
