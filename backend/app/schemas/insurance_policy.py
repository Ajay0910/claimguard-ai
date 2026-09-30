from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from .provenance import Provenance

def _parse_date(d_str: str) -> datetime:
    try:
        return datetime.fromisoformat(d_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            return datetime.strptime(d_str, '%d/%m/%Y')
        except ValueError:
            return datetime.strptime(d_str, '%d-%m-%Y')

class WaitingPeriodConfig(BaseModel):
    category: Provenance[Literal["INITIAL", "SPECIFIC_DISEASE", "PED"]]
    duration_days: Provenance[int]
    applicable_conditions: list[Provenance[str]]

class SubLimit(BaseModel):
    category: Provenance[str]
    max_amount: Optional[Provenance[float]] = None
    max_percentage: Optional[Provenance[float]] = None
    description: Provenance[str]

SubLimitConfig = SubLimit

class ProportionateDeductionRuleConfig(BaseModel):
    threshold_value: Provenance[float]
    threshold_operator: Provenance[str]
    threshold_source_type: Provenance[str]
    source_document_id: Optional[Provenance[str]] = None
    source_document_version: Optional[Provenance[str]] = None
    source_page: Optional[Provenance[int]] = None
    source_section: Optional[Provenance[str]] = None
    source_text: Optional[Provenance[str]] = None
    effective_date: Optional[Provenance[str]] = None
    policy_clause: Optional[Provenance[str]] = None
    applicability_conditions: Optional[Provenance[str]] = None

class InsurancePolicy(BaseModel):
    policy_number: Optional[Provenance[str]] = None
    insurer_name: Optional[Provenance[str]] = None
    policyholder_name: Optional[Provenance[str]] = None
    policy_version: Optional[Provenance[str]] = None
    deduction_order_clause: Optional[Provenance[str]] = None
    inception_date: Optional[Provenance[str]] = None
    policy_start_date: Optional[Provenance[str]] = None
    policy_end_date: Optional[Provenance[str]] = None
    sum_insured: Optional[Provenance[float]] = None
    room_rent_limit_per_day: Optional[Provenance[float]] = None
    room_category_entitled: Optional[Provenance[str]] = None
    copay_percentage: Provenance[float] = Provenance(value=0.0)
    deductible: Provenance[float] = Provenance(value=0.0)
    waiting_periods: list[WaitingPeriodConfig] = []
    sub_limits: list[SubLimit] = []
    covers_mental_health: Provenance[bool] = Provenance(value=True)
    
    covers_maternity: Provenance[bool] = Provenance(value=False)
    moratorium_period_months: Optional[Provenance[int]] = None
    portability_credits_months: Optional[Provenance[int]] = None
    migration_credits_months: Optional[Provenance[int]] = None
    enhanced_sum_insured: Optional[Provenance[float]] = None
    enhanced_sum_insured_date: Optional[Provenance[str]] = None
    proportionate_deduction_rule: Optional[ProportionateDeductionRuleConfig] = None
    exclusions: list[Provenance[str]] = []

    def evaluate_moratorium(self, claim_date: str, claim_amount: float) -> dict:
        """
        Evaluates the 60-month IRDAI moratorium (May 2024 Master Circular).
        Accounts for continuous coverage, portability credits, and enhanced sum insured.
        Returns detailed protection status.
        """
        try:
            from dateutil.relativedelta import relativedelta
            from app.rules import get_val
            
            start_date_str = get_val(self, 'inception_date', getattr(self, 'policy_start_date', None))
            if not start_date_str:
                return {"is_protected": False, "protected_amount": 0.0, "reason": "Missing policy inception date."}
                
            start = _parse_date(start_date_str)
            claim = _parse_date(claim_date)
            
            months_limit = get_val(self, 'moratorium_period_months', 60)
            portability_months = get_val(self, 'portability_credits_months', 0)
            migration_months = get_val(self, 'migration_credits_months', 0)
            total_credits = portability_months + migration_months
            
            # Exact calendar math: inception + (60 - portability_credits - migration_credits) months
            effective_moratorium_end = start + relativedelta(months=(months_limit - total_credits))
            
            is_base_protected = claim >= effective_moratorium_end
            
            base_si = get_val(self, 'sum_insured', 0.0)
            enhanced_si = get_val(self, 'enhanced_sum_insured', 0.0)
            
            # If there's an enhanced sum insured, it has its own 60 month timer
            enhanced_date_str = get_val(self, 'enhanced_sum_insured_date', None)
            if enhanced_date_str:
                current_start = _parse_date(enhanced_date_str)
            else:
                current_start = _parse_date(get_val(self, 'policy_start_date', start_date_str))
                
            enhanced_moratorium_end = current_start + relativedelta(months=months_limit)
            is_enhanced_protected = claim >= enhanced_moratorium_end
            
            protected_amount = 0.0
            if is_base_protected:
                if enhanced_si > 0 and not is_enhanced_protected:
                    # Only the original base SI is protected from PED/nondisclosure contestability
                    protected_amount = base_si - enhanced_si
                    reason = f"Base Sum Insured protected. Enhanced Sum Insured (Rs. {enhanced_si}) is still within its separate 60-month moratorium."
                else:
                    protected_amount = base_si
                    reason = "Full Sum Insured protected under continuous 60-month coverage (including portability)."
            else:
                reason = f"Claim date ({claim_date}) is before the effective moratorium completion date ({effective_moratorium_end.date()}). Not protected."
                
            return {
                "is_protected": is_base_protected,
                "protected_amount": protected_amount,
                "base_protected": is_base_protected,
                "enhanced_protected": is_enhanced_protected,
                "reason": reason
            }
            
        except Exception as e:
            return {"is_protected": False, "protected_amount": 0.0, "reason": f"Calculation error: {str(e)}"}

    def get_waiting_period_status(self, category: str, claim_date: str) -> dict:
        try:
            if not self.policy_start_date or not self.policy_start_date.value:
                return {"expired": False, "remaining_days": -1}
            start = _parse_date(self.policy_start_date.value)
            claim = _parse_date(claim_date)
            days_elapsed = (claim - start).days
            
            for wp in self.waiting_periods:
                if wp.category.value == category:
                    remaining = max(0, wp.duration_days.value - days_elapsed)
                    return {"expired": remaining == 0, "remaining_days": remaining}
            return {"expired": True, "remaining_days": 0}
        except Exception:
            return {"expired": False, "remaining_days": -1}
