import base64
import zlib
import urllib.request
import os
import glob
from PIL import Image

def encode_kroki(text):
    compressed = zlib.compress(text.encode('utf-8'), 9)
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii').replace('=', '')
    return b64

for mmd_file in glob.glob('*.mmd'):
    with open(mmd_file, 'r') as f:
        text = f.read()
    
    encoded = encode_kroki(text)
    url = f"https://kroki.io/mermaid/png/{encoded}"
    print(f"Fetching {mmd_file} from Kroki")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            png_data = response.read()
        
        png_name = mmd_file.replace('.mmd', '.png')
        with open(png_name, 'wb') as f:
            f.write(png_data)
        print(f"Saved {png_name}")
    except Exception as e:
        print(f"Failed {mmd_file}: {e}")
