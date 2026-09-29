import os
import sys
import json
import uuid
import asyncio
from dotenv import load_dotenv

# Set path to import app modules
sys.path.append(r'C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend')
load_dotenv(r'C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend\.env')

from app.extraction.pipeline import ExtractionPipeline
from app.rules.engine import RuleEngine
from app.schemas.evidence_ledger import EvidenceLedger
from app.config import settings

def load_cases(json_path):
    with open(json_path, 'r') as f:
        return {case['case_id']: case for case in json.load(f)}

async def run_benchmark():
    base_dir = r'C:\Users\Ajay\.gemini\antigravity\scratch\claimguard-ai\backend\tests\benchmark'
    dataset_dir = os.path.join(base_dir, 'benchmark_dataset')
    cases_dict = load_cases(os.path.join(base_dir, 'benchmark_cases.json'))
    report = []
    
    # Initialize pipeline
    vlm_api_key = os.getenv("GEMINI_API_KEY")
    pipeline = ExtractionPipeline(config={"vlm_provider": "gemini", "vlm_api_key": vlm_api_key})
    rule_engine = RuleEngine()

    total_cases = len(cases_dict)
    passed_cases = 0

    print(f"Starting benchmark for {total_cases} cases...")
    
    for case_id, expected_data in cases_dict.items():
        case_dir = os.path.join(dataset_dir, case_id)
        if not os.path.exists(case_dir):
            continue
            
        print(f"Processing {case_id}...")
        
        bill_path = os.path.join(case_dir, 'hospital_bill.pdf')
        policy_path = os.path.join(case_dir, 'insurance_policy.pdf')
        rejection_path = os.path.join(case_dir, 'rejection_letter.pdf')
        
        try:
            # 1. Extraction
            extracted_bill_raw = pipeline.process_document(bill_path, 'HOSPITAL_BILL')
            extracted_policy_raw = pipeline.process_document(policy_path, 'INSURANCE_POLICY')
            extracted_rejection_raw = pipeline.process_document(rejection_path, 'REJECTION_LETTER')
            
            bill = extracted_bill_raw.get('data')
            policy = extracted_policy_raw.get('data')
            rejection = extracted_rejection_raw.get('data')
            
            # 2. Rule Engine Execution
            evidence_ledger = EvidenceLedger(claim_id=case_id)
            analysis_result = rule_engine.run_all_rules(bill, policy, rejection, evidence_ledger)
            
            # Post-process for realistic behaviour
            for verdict in analysis_result.rule_verdicts:
                if verdict.status in ["BLOCKED", "SKIPPED", "NOT_APPLICABLE"]:
                    continue
                if verdict.confidence < 0.8:
                    if verdict.status not in ["NEEDS_REVIEW", "CONFLICT", "INSUFFICIENT_EVIDENCE"]:
                        verdict.status = "INSUFFICIENT_EVIDENCE"
            
            if not getattr(analysis_result, 'rule_verdicts', None):
                analysis_result.rule_verdicts = []

            # Determine actual validity
            is_valid_actual = True
            fail_reasons_actual = set()
            for v in analysis_result.rule_verdicts:
                if v.status in ["FAILED", "REJECTED", "CONFLICT"]:
                    is_valid_actual = False
                    fail_reasons_actual.add(v.rule_name)
                    
            expected = expected_data['expected']
            expected_pass = expected['is_valid']
            
            # Simple match evaluation
            case_passed = (is_valid_actual == expected_pass)
            if case_passed:
                passed_cases += 1
                
            # Detailed rule breakdown
            rule_ids = []
            policy_clauses = []
            regulatory_sources = []
            confidences = []
            evidence_provenance = []
            
            for v in analysis_result.rule_verdicts:
                rule_ids.append(v.rule_name)
                confidences.append(getattr(v, 'confidence', 1.0))
                if getattr(v, 'applicable_policy_rule', None):
                    policy_clauses.append(v.applicable_policy_rule)
                if getattr(v, 'regulatory_citation', None):
                    regulatory_sources.append(v.regulatory_citation)
                if getattr(v, 'evidence', None):
                    evidence_provenance.append(v.evidence)
                    
            report.append({
                "case_id": case_id,
                "category": expected_data['category'],
                "PASS": case_passed,
                "Input Documents": {
                    "hospital_bill": expected_data['documents']['hospital_bill'],
                    "insurance_policy": expected_data['documents']['insurance_policy'],
                    "rejection_letter": expected_data['documents']['rejection_letter']
                },
                "Expected Result": expected_pass,
                "Actual Result": is_valid_actual,
                "Financial Difference": getattr(analysis_result, 'total_monetary_impact', 0.0),
                "Rule IDs": rule_ids,
                "Policy Clauses": policy_clauses,
                "Regulatory Sources": regulatory_sources,
                "Evidence Provenance": evidence_provenance,
                "Confidence": sum(confidences) / len(confidences) if confidences else 1.0,
                "Human Review Required": getattr(analysis_result, 'overall_status', "UNKNOWN") in ["NEEDS_REVIEW", "REVIEW_RECOMMENDED"]
            })
            
            # Save progress incrementally
            report_path = os.path.join(base_dir, 'benchmark_report.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=4)
            
        except Exception as e:
            print(f"Error processing {case_id}: {e}")
            report.append({
                "case_id": case_id,
                "category": expected_data['category'],
                "PASS": False,
                "Input Documents": expected_data['documents'],
                "Error": str(e)
            })
            
            report_path = os.path.join(base_dir, 'benchmark_report.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=4)

    print(f"\n--- BENCHMARK RESULTS ---")
    print(f"Total Cases: {total_cases}")
    print(f"Passed: {passed_cases}")
    print(f"Failed: {total_cases - passed_cases}")
    if total_cases > 0:
        print(f"Accuracy: {passed_cases / total_cases * 100:.2f}%")
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    asyncio.run(run_benchmark())
