import hashlib
import os
import requests
from urllib.parse import urlparse

class ImageUtils:
    @staticmethod
    def extract_image_id(url):
        """
        Extracts the filename without extension from a URL to use as an ID.
        """
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            filename = os.path.basename(path)
            # Remove extension
            image_id = os.path.splitext(filename)[0]
            if not image_id:
                return hashlib.md5(url.encode()).hexdigest()
            return image_id
        except Exception:
            return hashlib.md5(url.encode()).hexdigest()

    @staticmethod
    def generate_unique_filename(url):
        """
        Generates a filename based on the ImageID extracted from the URL.
        """
        image_id = ImageUtils.extract_image_id(url)
        parsed_url = urlparse(url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1]
        if not ext:
            ext = '.jpg'
        if '?' in ext:
            ext = ext.split('?')[0]
        return f"{image_id}{ext}"

    @staticmethod
    def download_image(url, timeout=10):
        """
        Downloads an image from a URL and returns the content and suggested filename.
        """
        try:
            # Using verify=False to bypass SSL certificate verification issues
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(url, stream=True, timeout=timeout, verify=False)
            if response.status_code == 200:
                content = response.content
                
                # Determine extension
                parsed_url = urlparse(url)
                path = parsed_url.path
                ext = os.path.splitext(path)[1]
                if not ext or '?' in ext:
                    ext = '.jpg' # Default to jpg if unknown
                
                # Generate unique filename using hash of URL
                url_hash = hashlib.md5(url.encode()).hexdigest()
                filename = f"{url_hash}{ext}"
                
                return content, filename, response.headers.get('Content-Type', 'image/jpeg')
            else:
                print(f"Failed to download {url}: Status {response.status_code}")
                return None, None, None
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None, None, None
