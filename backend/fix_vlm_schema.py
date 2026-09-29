path = 'app/extraction/vlm_extractor.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old_str = 'generation_config={"response_mime_type": "application/json"}'
new_str = 'generation_config=self.client.types.GenerationConfig(response_mime_type="application/json", response_schema=schema_class)'
c = c.replace(old_str, new_str)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
