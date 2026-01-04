import os
from flask import jsonify
from modules.bigquery_utils import BigQueryUtils
from modules.gcs_utils import GCSUtils
from modules.image_utils import ImageUtils

def process_images(request):
    """
    Cloud Function entry point.
    """
    try:
        bq = BigQueryUtils()
        gcs = GCSUtils()
    except ValueError as e:
        return str(e), 500

    # 1. Get all source URLs
    source_urls = bq._get_all_source_urls()
    if not source_urls:
        return jsonify({"status": "success", "message": "No URLs found in source table."}), 200

    # 2. Get already processed ImageIDs
    processed_ids = bq.get_processed_image_ids()
    
    results = []
    processed_count = 0
    current_batch_ids = set()

    for url in source_urls:
        try:
            # Extract ImageID
            image_id = ImageUtils.extract_image_id(url)
            
            # Skip if already processed
            if image_id in processed_ids or image_id in current_batch_ids:
                continue
            
            current_batch_ids.add(image_id)

            # 3. Download image
            content, filename, content_type = ImageUtils.download_image(url)
            
            if content:
                # 4. Upload to GCS
                gcs_url = gcs.upload_to_gcs(content, filename, content_type)
                
                # 5. Record in BigQuery
                if bq.record_processed_url(url, gcs_url, image_id):
                    results.append({"url": url, "status": "success", "gcs_url": gcs_url, "image_id": image_id})
                    processed_count += 1
                else:
                    results.append({"url": url, "status": "failed_bq_record"})
            else:
                results.append({"url": url, "status": "failed_download"})
        except Exception as e:
            print(f"Error processing {url}: {e}")
            results.append({"url": url, "status": "error", "message": str(e)})

    return jsonify({
        "status": "success",
        "processed_count": processed_count,
        "results": results
    }), 200

if __name__ == "__main__":
    # For local testing
    class MockRequest:
        def get_json(self):
            return {}
    
    print(process_images(MockRequest()))
