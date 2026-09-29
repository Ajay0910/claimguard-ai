path = 'app/extraction/vlm_extractor.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('"gemini-1.5-flash"', '"gemini-2.5-flash"')
with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
