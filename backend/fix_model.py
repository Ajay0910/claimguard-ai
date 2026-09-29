path = 'app/config.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('"gemini-2.5-flash"', '"gemini-3.5-flash-lite"')
with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

path2 = 'app/extraction/vlm_extractor.py'
with open(path2, 'r', encoding='utf-8') as f:
    c2 = f.read()
c2 = c2.replace('"gemini-2.5-flash"', '"gemini-3.5-flash-lite"')
with open(path2, 'w', encoding='utf-8') as f:
    f.write(c2)
