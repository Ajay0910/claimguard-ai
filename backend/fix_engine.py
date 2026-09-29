import re
import sys

path = 'app/rules/engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports if they don't exist
imports = """import app.rules.proportionate_deduction
import app.rules.document_integrity
import app.rules.clause_timeline
import app.rules.mental_health_parity
import app.rules.waiting_period
import app.rules.appeal_evaluator
import app.rules.authenticity_check
import app.rules.identity_gate
import app.rules.clinical_firewall
"""

# Replace old imports
old_imports = """import app.rules.proportionate_deduction
import app.rules.document_integrity
import app.rules.clause_timeline
import app.rules.mental_health_parity
import app.rules.waiting_period
import app.rules.appeal_evaluator
import app.rules.authenticity_check"""

content = content.replace(old_imports, imports)

# Rewrite run_all_rules
new_run_all_rules = """
    def run_all_rules(self, bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> AnalysisResult:
        rules = get_all_rules()
        verdicts: List[RuleVerdict] = []
        
        # Split rules by tier
        tier_0_rules = [r for r in rules if r.get("tier", 1) == 0]
        other_rules = [r for r in rules if r.get("tier", 1) > 0]
        
        gate_blocked = False
        
        # Execute Gatekeepers
        for rule_info in tier_0_rules:
            func = rule_info["function"]
            try:
                verdict = func(bill, policy, rejection)
                verdicts.append(verdict)
                if verdict.status in ["NEEDS_REVIEW", "FAIL", "WARNING"]:
                    gate_blocked = True
            except Exception as e:
                verdicts.append(
                    RuleVerdict(
                        status="SKIPPED",
                        rule_name=rule_info["name"],
                        rule_description=rule_info.get("description", "Rule execution failed"),
                        confidence=1.0,
                        finding=f"Error running gatekeeper: {str(e)}"
                    )
                )
                
        # Execute remaining rules if gates pass
        for rule_info in other_rules:
            if gate_blocked:
                verdicts.append(
                    RuleVerdict(
                        status="SKIPPED",
                        rule_name=rule_info["name"],
                        rule_description=rule_info.get("description", ""),
                        confidence=1.0,
                        finding="Execution skipped because a Gatekeeper (Tier 0) rule failed."
                    )
                )
            else:
                func = rule_info["function"]
                try:
                    verdict = func(bill, policy, rejection)
                    verdicts.append(verdict)
                except Exception as e:
                    verdicts.append(
                        RuleVerdict(
                            status="SKIPPED",
                            rule_name=rule_info["name"],
                            rule_description=rule_info.get("description", "Rule execution failed"),
                            confidence=1.0,
                            finding=f"Error running rule: {str(e)}"
                        )
                    )
                
        has_fail = any(v.status == "FAIL" for v in verdicts)
        has_review = any(v.status == "NEEDS_REVIEW" for v in verdicts)
        
        if has_fail:
            overall_status = "MISMATCH_DETECTED"
        elif has_review:
            overall_status = "REVIEW_RECOMMENDED"
        else:
            overall_status = "NO_MISMATCH_FOUND"
            
        fail_count = sum(1 for v in verdicts if v.status == "FAIL")
        review_count = sum(1 for v in verdicts if v.status == "NEEDS_REVIEW")
        summary = f"Rule engine completed. {fail_count} failures, {review_count} needs review."
        
        # Evaluate appeal viability & Ombudsman risk
        appeal_result = None
        if rejection:
            claim_data = {
                "claim_id": getattr(bill, 'bill_id', None) or getattr(rejection, 'claim_number', ""),
                "claim_date": getattr(rejection, 'claim_date', None),
                "claimed_amount": getattr(rejection, 'total_claimed', 0.0),
                "approved_amount": getattr(rejection, 'total_approved', 0.0),
                "deducted_amount": getattr(rejection, 'total_deducted', 0.0),
                "diagnosis": getattr(bill, 'diagnosis', "") if bill else "",
            }
            policy_data = {
                "policy_start_date": getattr(policy, 'policy_start_date', None) if policy else None,
                "inception_date": getattr(policy, 'inception_date', getattr(policy, 'original_inception_date', None)) if policy else None,
                "moratorium_period_months": getattr(policy, 'moratorium_period_months', 60) if policy else 60,
                "covers_mental_health": getattr(policy, 'covers_mental_health', False) if policy else False,
            }
            appeal_result = self.appeal_evaluator.evaluate_verdicts(verdicts)
            
        return AnalysisResult(
            claim_id=bill.bill_id if hasattr(bill, 'bill_id') and bill.bill_id else "unknown_claim",
            analysis_timestamp=datetime.utcnow().isoformat(),
            documents_analyzed=[],
            overall_status=overall_status,
            summary=summary,
            rule_verdicts=verdicts,
            appeal_evaluation=appeal_result
        )
"""

old_run_all_rules_start = "    def run_all_rules(self, bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> AnalysisResult:"
old_run_all_rules_end = "    def run_single_rule"

start_idx = content.find(old_run_all_rules_start)
end_idx = content.find(old_run_all_rules_end)

new_content = content[:start_idx] + new_run_all_rules + "\n" + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
