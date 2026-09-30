import base64
import zlib
import urllib.request
import os
import glob
from PIL import Image
import io

def encode_mermaid(text):
    compressed = zlib.compress(text.encode('utf-8'), 9)
    # mermaid.ink requires URL-safe base64 encoding without padding
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii').replace('+', '-').replace('/', '_').rstrip('=')
    return b64

for mmd_file in glob.glob('*.mmd'):
    with open(mmd_file, 'r') as f:
        text = f.read()
    
    encoded = encode_mermaid(text)
    url = f"https://mermaid.ink/img/pako:{encoded}?type=png"
    print(f"Fetching {mmd_file} from {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            png_data = response.read()
        
        jpg_name = mmd_file.replace('.mmd', '.jpg')
        im = Image.open(io.BytesIO(png_data))
        rgb_im = im.convert('RGB')
        rgb_im.save(jpg_name, 'JPEG', quality=95)
        print(f"Saved {jpg_name}")
    except Exception as e:
        print(f"Failed {mmd_file}: {e}")
