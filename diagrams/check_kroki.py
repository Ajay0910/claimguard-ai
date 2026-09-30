import base64
import zlib
import urllib.request
import os
import glob
from PIL import Image
import io

def encode_kroki(text):
    compressed = zlib.compress(text.encode('utf-8'), 9)
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii')
    return b64

text = '''graph TD
A-->B'''
encoded = encode_kroki(text)
url = f"https://kroki.io/mermaid/jpeg/{encoded}"
print(url)
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        jpeg_data = response.read()
    print("Success")
except urllib.error.HTTPError as e:
    print(e.read())
