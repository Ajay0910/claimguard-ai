import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))

# Load .env file
load_dotenv()

from app.extraction.vlm_extractor import VLMExtractor

def test_extract():
    provider = os.getenv("VLM_PROVIDER", "gemini")
    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    
    if not api_key:
        print(f"ERROR: {provider.upper()}_API_KEY not found in .env")
        return
        
    extractor = VLMExtractor(provider=provider, api_key=api_key)
    bill_path = r"C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend\test.png"
    
    with open(bill_path, 'rb') as f:
        file_bytes = f.read()
        
    print(f"Extracting from {bill_path} using {provider}...")
    result = extractor.extract_hospital_bill(file_bytes, "image/png")
    
    print("EXTRACTION RESULT (JSON):")
    print(json.dumps(json.loads(result.model_dump_json()), indent=2))
    
    print("\n--- Testing Magic Methods on Ledger ---")
    print("Value:", result.total_amount.value)
    print("Direct Add (+100):", result.total_amount + 100)
    print("Direct Multiply (*2):", result.total_amount * 2)

if __name__ == "__main__":
    test_extract()
