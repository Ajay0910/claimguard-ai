import asyncio
from app.extraction.pipeline import ExtractionPipeline
import os
from dotenv import load_dotenv

load_dotenv()
pipeline = ExtractionPipeline({"use_vlm": True})
res = pipeline.process_claim_documents(
    "../test_docs/hard_test_hospital_bill.pdf",
    "../test_docs/hard_test_insurance_policy.pdf",
    "../test_docs/hard_test_rejection_letter.pdf"
)

import json
print(json.dumps(res['policy']['data'].model_dump(), indent=2))
