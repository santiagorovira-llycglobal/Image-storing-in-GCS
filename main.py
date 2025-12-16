import os
from datetime import datetime
from flask import jsonify
import functions_framework
import pandas as pd

# Import our modules
from modules import Config, StorageManager, BigQueryManager, SheetsManager


@functions_framework.http
def procesar_imagenes_sheet(request):
    """
    Cloud Function HTTP endpoint.
    Reads Google Sheets, checks for duplicates in GCS, uploads new images,
    and stores URLs in BigQuery.
    """
    
    print("=" * 80)
    print("Starting Image Processing Workflow")
    print("=" * 80)
    
    # 1. Initialize Configuration
    try:
        config = Config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Spreadsheet: {config.spreadsheet_key}")
        print(f"  - GCS Bucket: {config.gcs_bucket_name}")
        print(f"  - BigQuery Table: {config.get_bq_table_id()}")
    except Exception as e:
        error_msg = f"Configuration error: {str(e)}"
        print(f"✗ {error_msg}")
        return jsonify({"error": error_msg}), 500
    
    # 2. Initialize Managers
    try:
        sheets_manager = SheetsManager(config)
        storage_manager = StorageManager(config)
        bq_manager = BigQueryManager(config)
        print(f"✓ All managers initialized")
    except Exception as e:
        error_msg = f"Manager initialization error: {str(e)}"
        print(f"✗ {error_msg}")
        return jsonify({"error": error_msg}), 500
    
    # 3. Read Sheet Data
    try:
        print("\n" + "-" * 80)
        print("Reading Google Sheets data...")
        df = sheets_manager.read_sheet_data()
        print(f"✓ Read {len(df)} rows from sheet")
        
        if df.empty:
            return jsonify({"message": "Sheet is empty, nothing to process"}), 200
            
    except Exception as e:
        error_msg = f"Error reading sheet: {str(e)}"
        print(f"✗ {error_msg}")
        return jsonify({"error": error_msg}), 500
    
    # 4. Create BigQuery Table if needed
    try:
        print("\n" + "-" * 80)
        print("Ensuring BigQuery table exists...")
        bq_manager.create_table_if_not_exists()
        table_info = bq_manager.get_table_info()
        if table_info['exists']:
            print(f"✓ Table ready (current rows: {table_info.get('num_rows', 0)})")
    except Exception as e:
        error_msg = f"BigQuery table setup error: {str(e)}"
        print(f"✗ {error_msg}")
        return jsonify({"error": error_msg}), 500
    
    # 5. Process Images
    print("\n" + "-" * 80)
    print(f"Processing images from column: {config.url_column_name}")
    print("-" * 80)
    
    stats = {
        "total_rows": len(df),
        "skipped_empty": 0,
        "skipped_duplicate": 0,
        "uploaded": 0,
        "errors": 0,
        "error_details": []
    }
    
    bq_records = []
    
    for index, row in df.iterrows():
        url_imagen = row.get(config.url_column_name)
        
        # Skip empty URLs
        if not url_imagen or pd.isna(url_imagen) or str(url_imagen).strip() == "":
            stats["skipped_empty"] += 1
            continue
        
        # Generate filename
        filename = StorageManager.get_filename_from_url(url_imagen, index)
        blob_path = config.get_gcs_blob_path(filename)
        
        # Check if image already exists in GCS
        if storage_manager.check_image_exists(blob_path):
            print(f"  [{index}] ⊙ Already exists: {filename}")
            stats["skipped_duplicate"] += 1
            
            # Still add to BigQuery records (URL already stored)
            bq_records.append({
                'original_url': str(url_imagen),
                'gcs_url': storage_manager.get_public_url(blob_path),
                'filename': filename,
                'upload_timestamp': datetime.utcnow(),
                'row_index': int(index)
            })
            continue
        
        # Upload new image
        try:
            result = storage_manager.upload_image(url_imagen, blob_path)
            
            if result['success']:
                print(f"  [{index}] ✓ Uploaded: {filename}")
                stats["uploaded"] += 1
                
                # Add to BigQuery records
                bq_records.append({
                    'original_url': str(url_imagen),
                    'gcs_url': result['gcs_url'],
                    'filename': filename,
                    'upload_timestamp': datetime.utcnow(),
                    'row_index': int(index)
                })
            else:
                print(f"  [{index}] ✗ Failed: {result['error']}")
                stats["errors"] += 1
                stats["error_details"].append(f"Row {index}: {result['error']}")
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"  [{index}] ✗ {error_msg}")
            stats["errors"] += 1
            stats["error_details"].append(f"Row {index}: {error_msg}")
    
    # 6. Upload URLs to BigQuery
    print("\n" + "-" * 80)
    print(f"Uploading {len(bq_records)} records to BigQuery...")
    
    try:
        bq_result = bq_manager.upload_urls(bq_records)
        
        if bq_result['success']:
            print(f"✓ Successfully inserted {bq_result['rows_inserted']} rows into BigQuery")
        else:
            print(f"✗ BigQuery upload failed: {bq_result.get('error', 'Unknown error')}")
            stats["error_details"].append(f"BigQuery: {bq_result.get('error')}")
            
    except Exception as e:
        error_msg = f"BigQuery upload error: {str(e)}"
        print(f"✗ {error_msg}")
        stats["error_details"].append(error_msg)
    
    # 7. Final Summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total rows processed:    {stats['total_rows']}")
    print(f"Skipped (empty URL):     {stats['skipped_empty']}")
    print(f"Skipped (duplicate):     {stats['skipped_duplicate']}")
    print(f"Newly uploaded:          {stats['uploaded']}")
    print(f"Errors:                  {stats['errors']}")
    print("=" * 80)
    
    return jsonify({
        "status": "completed",
        "statistics": stats
    }), 200


# Local testing
if __name__ == "__main__":
    class MockRequest:
        pass
    
    print(procesar_imagenes_sheet(MockRequest()))
