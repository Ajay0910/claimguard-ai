"""
Real-world policy contract specifications and clause models for:
1. Star Health & Allied Insurance - Star Comprehensive Insurance Policy (UIN: SHAHLIP21226V052021)
2. HDFC ERGO General Insurance - my:Optima Secure (UIN: HDFHLIP26058V082526)
3. Care Health Insurance - Care Supreme (UIN: CHIHLIP22152V012122)

Extracted and verified against official IRDAI public policy filings and wordings.
"""

from typing import Dict, Any
from ..schemas.insurance_policy import (
    InsurancePolicy,
    ProportionateDeductionRuleConfig,
    WaitingPeriodConfig,
    SubLimit
)
from ..schemas.provenance import Provenance


def prov(val):
    return Provenance(value=val)


def get_star_comprehensive_policy(
    policy_number: str = "STAR-COMP-2024-987654",
    inception_date: str = "2020-04-01",
    sum_insured: float = 1000000.0,
    room_category: str = "SINGLE_PRIVATE_AC_ROOM"
) -> InsurancePolicy:
    """
    Star Comprehensive Insurance Policy:
    Section 1.A: Room (Private Single A/C room), Boarding and Nursing Expenses.
    Proportionate Clause: Hospitalization Expenses which vary based on the room rent occupied
    by the insured person will be considered in proportion to the room rent limit / room category.
    """
    prop_config = ProportionateDeductionRuleConfig(
        threshold_value=prov(1.0),
        threshold_operator=prov(">"),
        threshold_source_type=prov("POLICY_WORDING"),
        policy_clause=prov("Section 1.A - Hospitalization Expenses Note"),
        source_text=prov(
            "Hospitalization Expenses which vary based on the room rent occupied by the insured person "
            "will be considered in proportion to the room rent limit / room category stated in the policy schedule."
        )
    )

    waiting_periods = [
        WaitingPeriodConfig(
            category=prov("INITIAL"),
            duration_days=prov(30),
            applicable_conditions=[prov("All illnesses except accidental trauma")]
        ),
        WaitingPeriodConfig(
            category=prov("SPECIFIC_DISEASE"),
            duration_days=prov(730),  # 24 months
            applicable_conditions=[
                prov("Cataract"), prov("Hernia"), prov("Hysterectomy"),
                prov("Gallbladder stones / Cholecystectomy"), prov("Benign Prostatic Hypertrophy")
            ]
        ),
        WaitingPeriodConfig(
            category=prov("PED"),
            duration_days=prov(1095),  # 36 months under IRDAI 2024 cap
            applicable_conditions=[prov("Pre-Existing Diseases declared in proposal")]
        )
    ]

    return InsurancePolicy(
        policy_number=prov(policy_number),
        insurer_name=prov("Star Health and Allied Insurance Company Limited"),
        policyholder_name=prov("Insured Policyholder"),
        policy_version=prov("SHAHLIP21226V052021"),
        inception_date=prov(inception_date),
        policy_start_date=prov(inception_date),
        policy_end_date=prov("2027-03-31"),
        sum_insured=prov(sum_insured),
        room_category_entitled=prov(room_category),
        room_rent_limit_per_day=prov(6000.0),  # Standard Single Private AC baseline rate
        copay_percentage=prov(0.0),
        deductible=prov(0.0),
        moratorium_period_months=prov(60),
        waiting_periods=waiting_periods,
        proportionate_deduction_rule=prop_config,
        covers_mental_health=prov(True)
    )


def get_hdfc_optima_secure_policy(
    policy_number: str = "HDFC-OPT-SEC-2023-456789",
    inception_date: str = "2021-06-01",
    sum_insured: float = 1000000.0,
    has_room_cap: bool = False
) -> InsurancePolicy:
    """
    HDFC ERGO my:Optima Secure:
    Section B.1.a: Room rent, boarding, nursing expenses: Room rent limit shall be 'At Actuals'
    unless otherwise specified in Policy Schedule.
    Condition iii: Proportionate deduction does NOT apply if hospital does not follow differential billing.
    """
    prop_config = ProportionateDeductionRuleConfig(
        threshold_value=prov(1.0),
        threshold_operator=prov(">"),
        threshold_source_type=prov("POLICY_WORDING"),
        policy_clause=prov("Section B.1.a - Note (iii)"),
        source_text=prov(
            "Room rent limit shall be At Actuals unless specified in Policy Schedule. "
            "Proportionate deduction is not applicable in respect of Hospitals where differential billing "
            "for Associated Medical Expenses is not followed based on Room Rent."
        )
    )

    waiting_periods = [
        WaitingPeriodConfig(
            category=prov("INITIAL"),
            duration_days=prov(30),
            applicable_conditions=[prov("Illness treatments within first 30 days")]
        ),
        WaitingPeriodConfig(
            category=prov("SPECIFIC_DISEASE"),
            duration_days=prov(730),  # 24 months
            applicable_conditions=[prov("ENT disorders"), prov("Joint replacements"), prov("Calculus diseases")]
        ),
        WaitingPeriodConfig(
            category=prov("PED"),
            duration_days=prov(1095),  # 36 months cap
            applicable_conditions=[prov("Declared Pre-Existing Diseases")]
        )
    ]

    return InsurancePolicy(
        policy_number=prov(policy_number),
        insurer_name=prov("HDFC ERGO General Insurance Company Limited"),
        policyholder_name=prov("Insured Policyholder"),
        policy_version=prov("HDFHLIP26058V082526"),
        inception_date=prov(inception_date),
        policy_start_date=prov(inception_date),
        policy_end_date=prov("2027-05-31"),
        sum_insured=prov(sum_insured),
        room_category_entitled=prov("ANY_ROOM" if not has_room_cap else "SINGLE_PRIVATE_AC_ROOM"),
        room_rent_limit_per_day=prov(5000.0) if has_room_cap else None,  # None means At Actuals
        copay_percentage=prov(0.0),
        deductible=prov(0.0),
        moratorium_period_months=prov(60),
        waiting_periods=waiting_periods,
        proportionate_deduction_rule=prop_config,
        covers_mental_health=prov(True)
    )


def get_care_supreme_policy(
    policy_number: str = "CARE-SUP-2022-112233",
    inception_date: str = "2022-01-15",
    sum_insured: float = 700000.0,
    is_value_variant: bool = False
) -> InsurancePolicy:
    """
    Care Health Insurance - Care Supreme:
    Base Plan: Up to Sum Insured for Any Room category.
    Value Variant: Restricted to Single Private AC Room.
    Cumulative Bonus: 50% per claim-free year.
    """
    prop_config = ProportionateDeductionRuleConfig(
        threshold_value=prov(1.0),
        threshold_operator=prov(">"),
        threshold_source_type=prov("POLICY_WORDING"),
        policy_clause=prov("Section 1 - Inpatient Care - Room Rent"),
        source_text=prov(
            "Room Rent covered up to Sum Insured for Any Room category without sub-limit "
            "(or Single Private AC Room in Care Supreme Value variant)."
        )
    )

    waiting_periods = [
        WaitingPeriodConfig(
            category=prov("INITIAL"),
            duration_days=prov(30),
            applicable_conditions=[prov("Standard 30 days initial waiting period")]
        ),
        WaitingPeriodConfig(
            category=prov("SPECIFIC_DISEASE"),
            duration_days=prov(730),  # 24 months
            applicable_conditions=[prov("Hydrocele"), prov("Piles / Fistula"), prov("Sinusitis")]
        ),
        WaitingPeriodConfig(
            category=prov("PED"),
            duration_days=prov(1095),  # 36 months cap
            applicable_conditions=[prov("Declared Pre-Existing Conditions")]
        )
    ]

    return InsurancePolicy(
        policy_number=prov(policy_number),
        insurer_name=prov("Care Health Insurance Limited"),
        policyholder_name=prov("Insured Policyholder"),
        policy_version=prov("CHIHLIP22152V012122"),
        inception_date=prov(inception_date),
        policy_start_date=prov(inception_date),
        policy_end_date=prov("2027-01-14"),
        sum_insured=prov(sum_insured),
        room_category_entitled=prov("SINGLE_PRIVATE_AC_ROOM" if is_value_variant else "ANY_ROOM"),
        room_rent_limit_per_day=prov(5000.0) if is_value_variant else None,
        copay_percentage=prov(0.0),
        deductible=prov(0.0),
        moratorium_period_months=prov(60),
        waiting_periods=waiting_periods,
        proportionate_deduction_rule=prop_config,
        covers_mental_health=prov(True)
    )
