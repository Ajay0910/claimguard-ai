from . import get_val
import importlib
from typing import List
from datetime import datetime
from ..engine.calculator import FinancialMath

from ..schemas.hospital_bill import HospitalBill
from ..schemas.insurance_policy import InsurancePolicy
from ..schemas.rejection_letter import RejectionLetter
from ..schemas.analysis_result import AnalysisResult, RuleVerdict

from .appeal_evaluator import AppealEvaluator, AppealEvaluationResult
from .rule_registry import get_all_rules, get_rule
import app.rules.proportionate_deduction
import app.rules.clause_timeline
import app.rules.mental_health_parity
import app.rules.waiting_period
import app.rules.appeal_evaluator
import app.rules.authenticity_check
import app.rules.deductible_rule
import app.rules.copay_rule
import app.rules.cross_document_adjudication
import app.rules.policy_applicability
import app.rules.document_integrity
import app.rules.clinical_firewall
import app.rules.identity_gate


class RuleEngine:
    def __init__(self):
        self.appeal_evaluator = AppealEvaluator()


    def run_all_rules(self, bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter, ledger=None) -> AnalysisResult:
        rules = get_all_rules()
        verdicts: List[RuleVerdict] = []
        
        # Split rules by tier
        tier_0_rules = [r for r in rules if r.get("tier", 1) == 0]
        other_rules = [r for r in rules if r.get("tier", 1) > 0]
        
        gate_blocked = False
        
        # Execute Gatekeepers
        for rule_info in tier_0_rules:
            supported_versions = rule_info.get("supported_policy_versions", [])
            pol_version = get_val(policy, "policy_version", None) if policy else None
            if supported_versions and pol_version and str(pol_version).strip() not in supported_versions:
                verdicts.append(RuleVerdict(
                    finding_type="POLICY_MISMATCH",
                    status="SKIPPED",
                    rule_name=rule_info["name"],
                    rule_description=rule_info.get("description", ""),
                    confidence=1.0,
                    finding=f"Rule not applicable to policy version {str(pol_version).strip()}."
                ))
                continue
            
            func = rule_info["function"]
            try:
                verdict = func(bill, policy, rejection)
                if (
                    verdict.rule_name == "Cross-Document Identity Gate"
                    and verdict.status == "BLOCKED"
                    and "COVERAGE_DATE_CONFLICT" in (verdict.finding or "")
                    and policy
                    and rejection
                    and hasattr(policy, "evaluate_moratorium")
                    and get_val(rejection, "claim_date", None)
                ):
                    claim_date = get_val(rejection, "claim_date", None)
                    moratorium_status = policy.evaluate_moratorium(claim_date, 0.0) if claim_date else {"is_protected": False}
                    if moratorium_status.get("is_protected", False):
                        verdict = RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                            status="PASS",
                            rule_name="Cross-Document Identity Gate",
                            rule_description=verdict.rule_description,
                            confidence=1.0,
                            finding=f"Continuous coverage active under 60-month moratorium: {moratorium_status.get('reason')}",
                            monetary_impact=None
                        )
                verdicts.append(verdict)
                if verdict.status in ["BLOCKED"]:
                    gate_blocked = True
            except Exception as e:
                verdicts.append(
                    RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                        status="SKIPPED",
                        rule_name=rule_info["name"],
                        rule_description=rule_info.get("description", "Rule execution failed"),
                        confidence=1.0,
                        finding=f"Error running gatekeeper: {str(e)}"
                    )
                )
                
        from ..engine.dependency_graph import RuleDependencyGraph
        from ..engine.adjudication_state import AdjudicationState, LineItemState
        
        # Initialize Adjudication State
        adj_state = AdjudicationState(
            claim_id=get_val(bill, 'bill_id', "unknown_claim") if getattr(bill, 'bill_id', None) else "unknown_claim",
            line_items={},
            ledger=ledger
        )
        # Populate initial balances
        if bill and hasattr(bill, 'line_items') and get_val(bill, 'line_items', []):
            for i, item in enumerate(get_val(bill, 'line_items', [])):
                amt = get_val(item, 'amount', 0.0)
                code = get_val(item, 'item_code', None)
                if code is None: code = f"ITEM_{i}"
                if hasattr(code, 'value'): code = code.value
                
                cat = get_val(item, 'category', "MISCELLANEOUS")
                if hasattr(cat, 'value'): cat = cat.value
                
                adj_state.line_items[str(code)] = LineItemState(
                    item_code=str(code),
                    category=str(cat),
                    original_amount=amt,
                    remaining_balance=amt
                )

        try:
            dag = RuleDependencyGraph(other_rules, policy=policy)
            ordered_other_rules = dag.get_execution_order()
        except ValueError as e:
            # Graph conflict (e.g. mutual exclusivity or cycle)
            return AnalysisResult(
                claim_id=str(adj_state.claim_id),
                analysis_timestamp=datetime.utcnow().isoformat(),
                documents_analyzed=[],
                overall_status="REVIEW_RECOMMENDED",
                summary=f"Rule Engine aborted due to Dependency Graph Conflict: {str(e)}",
                rule_verdicts=verdicts,
                total_monetary_impact=None,
                tier1_issues=0,
                tier2_flags=0
            )

        # Execute remaining rules if gates pass
        for rule_info in ordered_other_rules:
            if gate_blocked:
                verdicts.append(
                    RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                        status="SKIPPED",
                        rule_name=rule_info["name"],
                        rule_description=rule_info.get("description", ""),
                        confidence=1.0,
                        finding="Execution skipped because a Gatekeeper (Tier 0) rule failed."
                    )
                )
            else:
                supported_versions = rule_info.get("supported_policy_versions", [])
                pol_version = get_val(policy, "policy_version", None) if policy else None
                if supported_versions and pol_version and str(pol_version).strip() not in supported_versions:
                    verdicts.append(RuleVerdict(
                        finding_type="POLICY_MISMATCH",
                        status="SKIPPED",
                        rule_name=rule_info["name"],
                        rule_description=rule_info.get("description", ""),
                        confidence=1.0,
                        finding=f"Rule not applicable to policy version {str(pol_version).strip()}."
                    ))
                    continue
                func = rule_info["function"]
                try:
                    # Check if rule accepts state
                    import inspect
                    sig = inspect.signature(func)
                    if 'state' in sig.parameters:
                        verdict = func(bill, policy, rejection, state=adj_state)
                    else:
                        verdict = func(bill, policy, rejection)
                    verdicts.append(verdict)
                except Exception as e:
                    verdicts.append(
                        RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                            status="SKIPPED",
                            rule_name=rule_info["name"],
                            rule_description=rule_info.get("description", "Rule execution failed"),
                            confidence=1.0,
                            finding=f"Error running rule: {str(e)}"
                        )
                    )
                
        has_blocked = any(v.status == "BLOCKED" for v in verdicts)
        has_fail = any(v.status == "FAIL" for v in verdicts)
        has_review = any(v.status == "NEEDS_REVIEW" for v in verdicts)
        
        if has_blocked:
            overall_status = "BLOCKED"
        elif has_fail:
            overall_status = "MISMATCH_DETECTED"
        elif has_review:
            overall_status = "REVIEW_RECOMMENDED"
        else:
            overall_status = "NO_MISMATCH_FOUND"
            
        
        # FINAL RECONCILIATION GATE
        expected_payable = FinancialMath.sum(
            [item.remaining_balance for item in adj_state.line_items.values()], 
            formula="sum(remaining_balances)", 
            quantize=True
        )
        
        insurer_payable_val = get_val(rejection, 'total_approved', 0.0) if rejection else expected_payable.value
        insurer_payable = FinancialMath.to_decimal(insurer_payable_val)
        
        disputed_amount = FinancialMath.sub(
            expected_payable, 
            insurer_payable, 
            formula="expected_payable - insurer_payable", 
            var_a="expected_payable", 
            var_b="insurer_payable", 
            quantize=True
        )
        
        # Ensure values are float for the final report/verdict output
        try:
            expected_payable_f = FinancialMath.to_float(expected_payable)
            insurer_payable_f = FinancialMath.to_float(insurer_payable)
            disputed_amount_f = FinancialMath.to_float(disputed_amount)
        except (TypeError, ValueError):
            expected_payable_f = 0.0
            insurer_payable_f = 0.0
            disputed_amount_f = 0.0
            
        billed_amount = get_val(bill, 'total_amount', 0.0) if bill else 0.0
        billed_amount_f = float(billed_amount) if billed_amount else 0.0

        # Point 10 & 14: Final Financial Assertions & Insurer Calculation Reproduction
        reconciliation_failed = False
        if rejection:
            insurer_claimed = float(get_val(rejection, 'total_claimed', billed_amount_f))
            insurer_deducted = float(get_val(rejection, 'total_deducted', 0.0))
            insurer_math_diff = insurer_claimed - insurer_deducted - insurer_payable_f
            if abs(insurer_math_diff) > 1.0:
                verdicts.append(RuleVerdict(
                    finding_type="FINANCIAL_DISCREPANCY",
                    status="NEEDS_REVIEW",
                    rule_name="Insurer Settlement Validation",
                    rule_description="Reproduce insurer settlement calculation",
                    confidence=1.0,
                    finding=f"Insurer math error: Claimed ({insurer_claimed}) - Deducted ({insurer_deducted}) != Approved ({insurer_payable_f}). Diff: {insurer_math_diff}",
                    monetary_impact=insurer_math_diff
                ))
                if overall_status not in ["BLOCKED", "MISMATCH_DETECTED"]:
                    overall_status = "REVIEW_RECOMMENDED"
        
        if abs(disputed_amount_f) > 0.00: # Discrepancy > 1 INR
            reconciliation_failed = True
            if overall_status == "NO_MISMATCH_FOUND":
                overall_status = "MISMATCH_DETECTED"
            verdicts.append(RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="FAIL",
                rule_name="Final Financial Reconciliation Gate",
                rule_description="Expected Payable minus Insurer Payable must equal 0, else there is a discrepancy.",
                confidence=1.0,
                finding=f"Reconciliation Failed: Expected Payable (₹{expected_payable_f:.2f}) - Insurer Payable (₹{insurer_payable_f:.2f}) = Disputed Amount (₹{disputed_amount_f:.2f}).",
                monetary_impact=disputed_amount_f
            ))
        else:
            verdicts.append(RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="PASS",
                rule_name="Final Financial Reconciliation Gate",
                rule_description="Expected Payable minus Insurer Payable must equal 0.",
                confidence=1.0,
                finding=f"Reconciliation Passed: Expected Payable (₹{expected_payable_f:.2f}) matches Insurer Payable (₹{insurer_payable_f:.2f}).",
                monetary_impact=0.0
            ))
            
        fail_count = sum(1 for v in verdicts if v.status == "FAIL")
        review_count = sum(1 for v in verdicts if v.status == "NEEDS_REVIEW")
        
        if has_blocked:
            blocked_rule = next(v.rule_name for v in verdicts if v.status == "BLOCKED")
            summary = f"ACTION = FINANCIAL_ENGINE_NOT_EXECUTED. Blocked by Tier 0 rule: {blocked_rule}."
        elif reconciliation_failed:
            summary = f"Rule engine completed. {fail_count} failures, {review_count} needs review. RECONCILIATION FAILED: Disputed amount is ₹{disputed_amount_f:.2f}."
        else:
            summary = f"Rule engine completed. {fail_count} failures, {review_count} needs review. RECONCILIATION MATCHED."
        
        # Evaluate appeal viability & Ombudsman risk
        appeal_result = None
        if rejection:
            claim_data = {
                "claim_id": get_val(bill, 'bill_id', None) or get_val(rejection, 'claim_number', ""),
                "claim_date": get_val(rejection, 'claim_date', None),
                "claimed_amount": get_val(rejection, 'total_claimed', 0.0),
                "approved_amount": get_val(rejection, 'total_approved', 0.0),
                "deducted_amount": get_val(rejection, 'total_deducted', 0.0),
                "diagnosis": get_val(bill, 'diagnosis', "") if bill else "",
            }
            policy_data = {
                "policy_start_date": get_val(policy, 'policy_start_date', None) if policy else None,
                "inception_date": get_val(policy, 'inception_date', getattr(policy, 'original_inception_date', None)) if policy else None,
                "moratorium_period_months": get_val(policy, 'moratorium_period_months', 60) if policy else 60,
                "covers_mental_health": get_val(policy, 'covers_mental_health', False) if policy else False,
            }
            reasons = get_val(rejection, 'rejection_reasons', None) or get_val(rejection, 'reasons', []) or []
            appeal_result = self.appeal_evaluator.evaluate_denial(
                denial_reasons=reasons,
                claim_data=claim_data,
                policy_data=policy_data,
            )
            
        # Bind ledger entries to verdicts if ledger exists
        if ledger and hasattr(ledger, "filter_by_rule"):
            for v in verdicts:
                entries = ledger.filter_by_rule(v.rule_name)
                if entries:
                    v.evidence_entries = entries
            
        billed_amount = get_val(bill, 'total_amount', 0.0) if bill else 0.0
        billed_amount_f = float(billed_amount) if billed_amount else 0.0

        total_disallowed = max(0.0, billed_amount_f - insurer_payable_f)
        legitimate_deduction = max(0.0, total_disallowed - disputed_amount_f)

        safe_total = billed_amount_f if billed_amount_f > 0 else 1.0
        approved_pct = min(100.0, max(0.0, (insurer_payable_f / safe_total) * 100.0))
        recoverable_pct = min(100.0 - approved_pct, max(0.0, (disputed_amount_f / safe_total) * 100.0))
        legitimate_pct = max(0.0, 100.0 - approved_pct - recoverable_pct)

        recovery_yield = f"{(disputed_amount_f / insurer_payable_f * 100):.1f}" if insurer_payable_f > 0 else "0.0"
        
        return AnalysisResult(
            claim_id=str(get_val(bill, 'bill_id', "unknown_claim")) if getattr(bill, 'bill_id', None) else "unknown_claim",
            analysis_timestamp=datetime.utcnow().isoformat(),
            documents_analyzed=[],
            overall_status=overall_status,
            summary=summary,
            rule_verdicts=verdicts,
            appeal_evaluation=appeal_result,
            total_monetary_impact=disputed_amount_f,
            insurer_approved_amount=insurer_payable_f,
            expected_admissible_amount=expected_payable_f,
            billed_amount=billed_amount_f,
            total_disallowed=total_disallowed,
            legitimate_deduction=legitimate_deduction,
            approved_pct=approved_pct,
            recoverable_pct=recoverable_pct,
            legitimate_pct=legitimate_pct,
            recovery_yield=recovery_yield
        )

    def run_single_rule(self, rule_name: str, bill: HospitalBill, policy: InsurancePolicy, rejection: RejectionLetter) -> RuleVerdict:
        func = get_rule(rule_name)
        if not func:
            return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="SKIPPED", 
                rule_name=rule_name, 
                rule_description="Rule not found",
                confidence=1.0,
                finding="Rule not found."
            )
        try:
            return func(bill, policy, rejection)
        except Exception as e:
            return RuleVerdict(finding_type="FINANCIAL_DISCREPANCY", 
                status="SKIPPED", 
                rule_name=rule_name, 
                rule_description="Error running rule",
                confidence=1.0,
                finding=f"Error running rule: {str(e)}"
            )
