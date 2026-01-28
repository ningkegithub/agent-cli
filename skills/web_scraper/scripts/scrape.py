import argparse
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_images(url, output_dir):
    try:
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        print(f"Fetching: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')
        
        print(f"Found {len(images)} images.")

        count = 0
        for i, img in enumerate(images, start=1):
            img_src = img.get('src')
            if not img_src:
                continue

            # Handle relative URLs
            img_url = urljoin(url, img_src)
            
            # Basic filter: skip small icons or base64 (optional)
            if img_url.startswith('data:'):
                continue

            try:
                # Get filename from URL or generate one
                parsed = urlparse(img_url)
                filename = os.path.basename(parsed.path)
                if not filename or '.' not in filename:
                    filename = f"image_{i:03d}.jpg"
                else:
                    # Prefix to ensure order
                    filename = f"img_{i:03d}_{filename}"
                
                # Sanitize filename
                filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._-'])

                filepath = os.path.join(output_dir, filename)
                
                print(f"Downloading {i}: {img_url}")
                img_data = requests.get(img_url, timeout=5).content
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                count += 1
                
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")

        print(f"Successfully downloaded {count} images to '{output_dir}'.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape images from a URL.")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("output_dir", nargs="?", default=".", help="Output directory")
    args = parser.parse_args()

    scrape_images(args.url, args.output_dir)
