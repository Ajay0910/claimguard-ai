import uuid
import datetime
from typing import Dict, Any, List, Optional

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
        pdf.set_font("Helvetica", size=10)
        
        for line in appeal_text.split('\n'):
            # Convert simple markdown bold back to text for FPDF to avoid printing **
            clean_line = line.replace('**', '')
            # replace rupee symbol for basic PDF compatibility
            clean_line = clean_line.replace('₹', 'Rs. ')
            # Fallback encode decode to ascii to ignore unexpected chars
            try:
                pdf.multi_cell(0, 5, text=clean_line, align="L", new_x="LMARGIN", new_y="NEXT")
            except TypeError:
                pdf.multi_cell(0, 5, txt=clean_line, align="L")
                pdf.set_x(getattr(pdf, "l_margin", 10))
            
        pdf.output(output_path)
        return output_path

    def generate_ombudsman_form_via(
        self,
        complaint_data_or_analysis: Any,
        bill: Any = None,
        policy: Any = None,
        rejection: Any = None,
        pincode: Optional[str] = None,
        output_pdf_path: Optional[str] = None
    ) -> dict:
        """
        Generate statutory Insurance Ombudsman Form VI-A text and optional PDF.
        Supports both direct complaint_data dict and model-based signature:
        (analysis_res, bill, policy, rejection, pincode, output_pdf_path)
        """
        import datetime
        from .ombudsman_form_generator import OmbudsmanFormGenerator, map_pincode_to_ombudsman
        generator = OmbudsmanFormGenerator()

        def _val(obj, attr, default=""):
            if not obj:
                return default
            v = getattr(obj, attr, None)
            if v is None and isinstance(obj, dict):
                v = obj.get(attr)
            if hasattr(v, 'value'):
                return v.value if v.value is not None else default
            return v if v is not None else default

        if isinstance(complaint_data_or_analysis, dict) and bill is None and policy is None and rejection is None:
            complaint_data = dict(complaint_data_or_analysis)
        else:
            analysis = complaint_data_or_analysis
            patient_name = _val(bill, 'patient_name') or _val(policy, 'policyholder_name') or "Insured / Policyholder"
            insurer = _val(policy, 'insurer_name') or _val(rejection, 'insurer_name') or "Insurance Company Ltd."
            pol_num = _val(policy, 'policy_number') or "POL-XXXXXX"
            claim_num = _val(rejection, 'claim_number') or "CLM-XXXXXX"
            rep_date = _val(rejection, 'claim_date') or str(datetime.date.today().isoformat())
            
            disputed = 0.0
            if hasattr(analysis, 'total_monetary_impact') and analysis.total_monetary_impact is not None:
                disputed = float(analysis.total_monetary_impact)
            elif isinstance(analysis, dict):
                disputed = float(analysis.get('total_monetary_impact') or 0.0)

            grounds = []
            verdicts = getattr(analysis, 'rule_verdicts', []) if hasattr(analysis, 'rule_verdicts') else (analysis.get('rule_verdicts', []) if isinstance(analysis, dict) else [])
            for v in verdicts:
                status = getattr(v, 'status', None) or (v.get('status') if isinstance(v, dict) else None)
                finding = getattr(v, 'finding', None) or (v.get('finding') if isinstance(v, dict) else "")
                if status == "FAIL" and finding:
                    grounds.append(str(finding))
            grounds_text = "; ".join(grounds) if grounds else "Unlawful deduction and statutory breach of IRDAI regulations."

            complaint_data = {
                "complainant_name": patient_name,
                "complainant_address": _val(bill, 'hospital_address', "Resident Address"),
                "pincode": pincode or "400001",
                "insurer_name": insurer,
                "policy_number": pol_num,
                "claim_number": claim_num,
                "repudiation_date": rep_date,
                "disputed_amount": disputed,
                "grounds_summary": grounds_text
            }

        form_text = generator.generate_form_via_text(complaint_data)
        pdf_path = None
        if output_pdf_path:
            pdf_path = generator.generate_form_via_pdf(complaint_data, output_pdf_path)
        resolved_pin = str(complaint_data.get("pincode", pincode or "400001"))
        jurisdiction = map_pincode_to_ombudsman(resolved_pin)
        return {
            "form_text": form_text,
            "pdf_path": pdf_path,
            "jurisdiction": jurisdiction
        }

    def generate_predischarge_alert(self, simulation_result: Any) -> dict:
        """
        Formats pre-discharge simulation result into an actionable patient advisory packet.
        """
        if hasattr(simulation_result, "to_dict"):
            data = simulation_result.to_dict()
        elif hasattr(simulation_result, "model_dump"):
            data = simulation_result.model_dump()
        elif isinstance(simulation_result, dict):
            data = dict(simulation_result)
        else:
            data = {}

        return {
            "is_interim": data.get("is_interim", True),
            "has_room_rent_excess": data.get("has_room_rent_excess", False),
            "room_rate": data.get("actual_room_rate", 0.0),
            "eligible_room_rate": data.get("eligible_room_rate", 0.0),
            "projected_room_excess": data.get("projected_room_excess", 0.0),
            "projected_proportionate_deduction": data.get("projected_proportionate_deduction", 0.0),
            "projected_total_out_of_pocket": data.get("projected_total_out_of_pocket", 0.0),
            "warning_message": data.get("warning_message", ""),
            "recommended_action": data.get("recommended_action", ""),
            "scrubbed_non_payable_items": data.get("scrubbed_non_payable_items", []),
            "total_scrubbed_non_payables": data.get("total_scrubbed_non_payables", 0.0),
        }
