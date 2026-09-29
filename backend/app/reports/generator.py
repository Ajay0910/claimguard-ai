import uuid
import datetime
from typing import Dict, Any, List

from jinja2 import Environment, BaseLoader

try:
    from fpdf import FPDF
except ImportError:
    class FPDF:
        def __init__(self, *args, **kwargs): pass
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def output(self, *args, **kwargs): pass

from ..schemas.analysis_result import AnalysisResult, RuleVerdict
from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from .templates.appeal_template import APPEAL_LETTER_TEMPLATE, REPORT_SUMMARY_TEMPLATE, indian_currency_filter


class ReportGenerator:
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        self.env.filters['indian_currency'] = indian_currency_filter

    def generate_analysis_report(self, analysis: AnalysisResult, bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> dict:
        """
        Generate a comprehensive analysis report as a structured dict.
        Returns:
        {
            'report_id': str,
            'generated_at': str (ISO),
            'claim_summary': {...},
            'document_summary': {...},
            'tier1_findings': [...],
            'tier2_flags': [...],
            'overall_assessment': str,
            'monetary_impact_summary': {
                'total_claimed': float,
                'insurer_approved': float,
                'correct_payable': float,
                'underpayment': float
            },
            'recommendations': [...],
            'regulatory_citations': [...]
        }
        """
        tier1_findings = [r for r in analysis.rule_verdicts if r.status == "FAIL"]
        tier2_flags = [r for r in analysis.rule_verdicts if r.status == "WARNING"]
        
        total_claimed = float(getattr(bill, 'total_amount', 0.0))
        insurer_approved = float(getattr(rejection, 'approved_amount', 0.0))
        
        impacts = [getattr(f, 'monetary_impact', None) for f in tier1_findings]
        if any(impact is None for impact in impacts) and len(impacts) > 0:
            underpayment = None
            correct_payable = None
        else:
            underpayment = sum(float(i) for i in impacts) if impacts else 0.0
            correct_payable = insurer_approved + underpayment

        report_id = str(uuid.uuid4())
        generated_at = datetime.datetime.utcnow().isoformat()
        
        recommendations = [f.appeal_recommendation for f in tier1_findings if hasattr(f, 'appeal_recommendation') and f.appeal_recommendation]
        regulatory_citations = [f.regulatory_citation for f in tier1_findings if hasattr(f, 'regulatory_citation') and f.regulatory_citation]
        
        overall_assessment = "Requires Appeal" if tier1_findings else "Claim processing appears correct"
        
        return {
            'report_id': report_id,
            'generated_at': generated_at,
            'claim_summary': {
                'policy_number': getattr(policy, 'policy_number', 'N/A'),
                'claim_number': getattr(rejection, 'claim_number', 'N/A'),
            },
            'document_summary': {
                'bill_id': getattr(bill, 'bill_id', 'N/A'),
                'rejection_id': getattr(rejection, 'rejection_id', 'N/A'),
            },
            'tier1_findings': [f.model_dump() if hasattr(f, 'model_dump') else dict(f) for f in tier1_findings],
            'tier2_flags': [f.model_dump() if hasattr(f, 'model_dump') else dict(f) for f in tier2_flags],
            'overall_assessment': overall_assessment,
            'monetary_impact_summary': {
                'total_claimed': total_claimed,
                'insurer_approved': insurer_approved,
                'correct_payable': correct_payable,
                'underpayment': underpayment
            },
            'recommendations': recommendations,
            'regulatory_citations': regulatory_citations
        }

    def generate_appeal_letter(self, analysis: AnalysisResult, bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> str:
        """
        Generate a formal appeal letter text addressed to the insurer/ombudsman.
        
        The letter should follow this structure:
        1. Header: From (patient), To (insurer grievance cell)
        2. Subject: Appeal against Claim No. X dated Y
        3. Reference: Policy number, claim number, rejection letter reference
        4. Body:
           a. Statement of facts (admission, treatment, billing)
           b. For EACH mismatch found (status==FAIL):
              - What the insurer did wrong
              - The correct calculation with step-by-step math
              - The specific IRDAI regulation violated
              - The monetary impact
           c. Summary of total underpayment
           d. Legal basis citing specific acts and clauses
        5. Prayer: Request for reconsideration and payment of differential amount
        6. Closing: Mention right to approach Insurance Ombudsman / IRDAI GRO
        
        Use formal Indian legal letter format.
        """
        findings = [
            r for r in analysis.rule_verdicts 
            if r.status == "FAIL" and len(r.evidence_entries) > 0
        ]
        
        if not findings:
            return "No grounds for appeal found, or findings lack sufficient validated evidence ledger entries."
            
        template = self.env.from_string(APPEAL_LETTER_TEMPLATE)
        
        impacts = [getattr(f, 'monetary_impact', None) for f in findings]
        if any(impact is None for impact in impacts) and len(impacts) > 0:
            total_impact = None
        else:
            total_impact = sum(float(i) for i in impacts) if impacts else 0.0
        
        policy_number = getattr(policy, 'policy_number', 'N/A')
        claim_number = getattr(rejection, 'claim_number', 'N/A')
        claim_date = getattr(rejection, 'claim_date', 'N/A')
        patient_name = getattr(policy, 'policy_holder_name', 'Patient Name')
        insurer_name = getattr(policy, 'insurer_name', 'Insurance Company')
        
        settlement_type = "Partial Settlement" if getattr(rejection, 'approved_amount', 0.0) > 0 else "Rejection"
        total_amount = getattr(bill, 'total_amount', 'X')
        
        facts_section = f"I was admitted to the hospital and incurred a total bill of Rs {total_amount}. The claim was processed on {claim_date}, but wrongfully settled/rejected."
        legal_basis = "As per IRDAI (Protection of Policyholders' Interests) Regulations, 2017, the insurer must process claims transparently and justify any deductions with specific policy clauses."
        prayer_section = "I request you to re-evaluate the claim deductions and release the differential amount as detailed above immediately."
        
        context = {
            'date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'insurer_name': insurer_name,
            'insurer_address': "Grievance Department",
            'settlement_type': settlement_type,
            'claim_number': claim_number,
            'policy_number': policy_number,
            'patient_name': patient_name,
            'claim_date': claim_date,
            'facts_section': facts_section,
            'findings': findings,
            'total_impact': total_impact,
            'legal_basis': legal_basis,
            'prayer_section': prayer_section,
            'contact_info': "Email/Phone"
        }
        
        return template.render(**context)

    def generate_appeal_pdf(self, appeal_text: str, output_path: str) -> str:
        """
        Convert appeal letter text to a professional PDF using fpdf2.
        Returns the output file path.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        
        for line in appeal_text.split('\n'):
            # Convert simple markdown bold back to text for FPDF to avoid printing **
            clean_line = line.replace('**', '')
            # replace rupee symbol for basic PDF compatibility
            clean_line = clean_line.replace('₹', 'Rs. ')
            # Fallback encode decode to ascii to ignore unexpected chars
            clean_line = clean_line.encode('ascii', 'ignore').decode('ascii')
            pdf.multi_cell(0, 5, txt=clean_line, align="L")
            
        pdf.output(output_path)
        return output_path
