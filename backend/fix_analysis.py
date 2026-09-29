import os
path = 'app/api/analysis.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old_str = 'vlm_api_key = settings.OPENAI_API_KEY if settings.VLM_PROVIDER == "openai" else settings.ANTHROPIC_API_KEY'
new_str = 'vlm_api_key = settings.OPENAI_API_KEY if settings.VLM_PROVIDER == "openai" else (settings.GEMINI_API_KEY if settings.VLM_PROVIDER == "gemini" else settings.ANTHROPIC_API_KEY)'

c = c.replace(old_str, new_str)
with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
