import os
import urllib.request

ASSETS = {
    "tabulator/tabulator.min.js": "https://unpkg.com/tabulator-tables@6.2.1/dist/js/tabulator.min.js",
    "tabulator/tabulator.min.css": "https://unpkg.com/tabulator-tables@6.2.1/dist/css/tabulator.min.css",
    "tom-select/tom-select.complete.min.js": "https://cdn.jsdelivr.net/npm/tom-select@2.4.1/dist/js/tom-select.complete.min.js",
    "tom-select/tom-select.css": "https://cdn.jsdelivr.net/npm/tom-select@2.4.1/dist/css/tom-select.css",
    "alpinejs/alpine.min.js": "https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js",
    "fonts/inter-400.woff2": "https://cdn.jsdelivr.net/npm/@fontsource/inter/files/inter-latin-400-normal.woff2",
    "fonts/inter-600.woff2": "https://cdn.jsdelivr.net/npm/@fontsource/inter/files/inter-latin-600-normal.woff2"
}

def download_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for rel_path, url in ASSETS.items():
        dest_path = os.path.join(base_dir, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        print(f"Downloading {url} -> {rel_path}...")
        try:
            # Add a generic user agent to bypass any bot protections
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Successfully downloaded {rel_path}")
        except Exception as e:
            print(f"Failed to download {rel_path}: {e}")

if __name__ == "__main__":
    download_all()
