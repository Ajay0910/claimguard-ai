import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
from backend.app.extraction.pipeline import ExtractionPipeline
import logging
logging.basicConfig(level=logging.DEBUG)

api_key = os.getenv('GEMINI_API_KEY')
pipeline = ExtractionPipeline(config={'vlm_provider': 'gemini', 'vlm_api_key': api_key})

try:
    with open('backend/tests/fixtures/synthetic_policy.pdf', 'rb') as pdf_file:
        res = pipeline.extract(pdf_file.read(), 'application/pdf', 'INSURANCE_POLICY')
        print('Source:', res.get('source'))
        print('Status:', res.get('status'))
        print('Issues:', res.get('issues'))
except Exception as e:
    print('Exception:', e)
