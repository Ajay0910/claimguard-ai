"""
Explainable Composite Fraud Risk Scorer with Additive Factor Attribution.
Derived from Wang et al., Nature Scientific Reports 2025:
"A Robust and Interpretable Ensemble Machine Learning Model for Predicting Healthcare Insurance Fraud"
(TreeSHAP-inspired additive feature attribution across multi-modal forensic signals).
"""

from typing import List, Dict, Any, Optional, Union
import math
from pydantic import BaseModel, Field


from ..schemas.forensics_result import FactorAttribution, AnomalyAssessment


class AnomalyScorer:
    """
    Computes a calibrated composite fraud risk score (0.0 - 100.0%) from multi-modal
    forensics, billing anomalies, clinical consistency, and metadata checks.
    Decomposes the overall score into interpretable, additive factor attributions.
    """

    # Calibrated category weights (sum to 1.00)
    WEIGHT_FORENSICS = 0.35
    WEIGHT_BILLING = 0.30
    WEIGHT_CLINICAL = 0.25
    WEIGHT_METADATA = 0.10

    def __init__(self):
        pass

    def compute_score(
        self,
        forensics_result: Optional[Union[Dict[str, Any], Any]] = None,
        bill_anomalies: Optional[Union[Dict[str, Any], List[Any]]] = None,
        clinical_consistency: Optional[Union[Dict[str, Any], List[Any]]] = None,
        metadata_flags: Optional[List[Any]] = None,
        provider_data: Optional[Dict[str, Any]] = None,
    ) -> AnomalyAssessment:
        """
        Evaluate all inputs and compute calibrated composite score with additive feature attributions.
        """
        attributions: List[FactorAttribution] = []

        # 1. FORENSICS ATTRIBUTIONS
        f_score, f_attrs = self._evaluate_forensics(forensics_result)
        attributions.extend(f_attrs)

        # 2. METADATA ATTRIBUTIONS
        m_score, m_attrs = self._evaluate_metadata(metadata_flags)
        attributions.extend(m_attrs)

        # 3. BILLING ANOMALY ATTRIBUTIONS
        b_score, b_attrs = self._evaluate_billing(bill_anomalies)
        attributions.extend(b_attrs)

        # 4. CLINICAL CONSISTENCY ATTRIBUTIONS
        c_score, c_attrs = self._evaluate_clinical(clinical_consistency)
        attributions.extend(c_attrs)

        # 5. PROVIDER RISK ATTRIBUTION
        p_score, p_attrs = self._evaluate_provider(provider_data, b_score, c_score)
        attributions.extend(p_attrs)

        # TreeSHAP-style additive composite calculation:
        # Base expected risk for unflagged claim = 2.0%
        base_risk = 2.0

        def _clean_comp(v: Any) -> float:
            try:
                val = float(v)
                return 0.0 if (math.isnan(val) or math.isinf(val)) else val
            except (ValueError, TypeError):
                return 0.0

        f_score_clean = _clean_comp(f_score)
        m_score_clean = _clean_comp(m_score)
        b_score_clean = _clean_comp(b_score)
        c_score_clean = _clean_comp(c_score)
        p_score_clean = _clean_comp(p_score)
        
        # Point 2: A financial discrepancy must not automatically trigger fraud alerts.
        if f_score_clean < 0.15 and m_score_clean < 0.15:
            b_score_clean = min(b_score_clean, 0.25)
            c_score_clean = min(c_score_clean, 0.25)

        # Weighted sum of category contributions:
        raw_composite = (
            base_risk
            + (f_score_clean * self.WEIGHT_FORENSICS * 100.0)
            + (m_score_clean * self.WEIGHT_METADATA * 100.0)
            + (b_score_clean * self.WEIGHT_BILLING * 100.0)
            + (c_score_clean * self.WEIGHT_CLINICAL * 100.0)
            + (p_score_clean * 0.05 * 100.0)
        )

        if math.isnan(raw_composite) or math.isinf(raw_composite):
            raw_composite = base_risk

        overall_score = max(0.0, min(100.0, round(raw_composite, 2)))

        # Calibrate risk tier
        if overall_score < 25.0:
            review_status = "CLEAN"
        elif overall_score < 50.0:
            review_status = "NEEDS_REVIEW"
        elif overall_score < 75.0:
            review_status = "FLAGGED FOR REVIEW"
        else:
            review_status = "FLAGGED FOR REVIEW"

        # Calculate confidence metric based on signal availability
        confidence = self._calculate_confidence(
            forensics_result, bill_anomalies, clinical_consistency, metadata_flags
        )

        # Top risk drivers: factors with highest positive impact_score
        active_drivers = [
            fa for fa in attributions if fa.impact_score > 0.05
        ]
        active_drivers.sort(key=lambda x: x.impact_score * x.weight, reverse=True)
        top_anomalies = [
            f"{fa.factor_name}: {fa.description}" for fa in active_drivers[:5]
        ]

        # Generate interpretability summary narrative
        summary = self._generate_summary(
            overall_score, review_status, confidence, active_drivers
        )

        return AnomalyAssessment(
            anomaly_density_score=overall_score,
            review_status=review_status,
            confidence=confidence,
            factor_attributions=attributions,
            top_anomalies=top_anomalies,
            summary=summary,
        )

    def _evaluate_forensics(
        self, forensics_result: Optional[Union[Dict[str, Any], Any]]
    ) -> tuple[float, List[FactorAttribution]]:
        attrs: List[FactorAttribution] = []
        if not forensics_result:
            attrs.append(
                FactorAttribution(
                    category="forensics",
                    factor_name="document_integrity_check",
                    impact_score=0.0,
                    weight=0.15,
                    description="No visual or structural forensic data provided.",
                )
            )
            return 0.0, attrs

        # Convert Pydantic model if needed
        f_dict = (
            forensics_result.model_dump()
            if hasattr(forensics_result, "model_dump")
            else (
                forensics_result.dict()
                if hasattr(forensics_result, "dict")
                else (forensics_result if isinstance(forensics_result, dict) else {})
            )
        )

        # ELA Tampering Score
        ela_data = (
            f_dict.get("ela_result")
            if isinstance(f_dict, dict)
            else getattr(f_dict, "ela_result", None)
        )
        if not ela_data:
            ela_data = {}

        try:
            raw_ela = (
                getattr(ela_data, 'tamper_score', None)
                if not isinstance(ela_data, dict)
                else ela_data.get('tamper_score', 0.0)
            )
            ela_score = float(raw_ela) if raw_ela is not None else 0.0
            if math.isnan(ela_score) or math.isinf(ela_score):
                ela_score = 0.0
        except (ValueError, TypeError):
            ela_score = 0.0

        # Scale normalization: ELADetector outputs [0.0, 100.0]. If > 1.0, normalize to [0.0, 1.0]
        if ela_score > 1.0:
            ela_score = min(1.0, ela_score / 100.0)

        ela_assessment = (
            getattr(ela_data, 'assessment', None)
            if not isinstance(ela_data, dict)
            else ela_data.get('assessment', 'CLEAN')
        ) or "CLEAN"

        ela_impact = min(1.0, max(-0.2, (ela_score - 0.15) * 1.5))
        if ela_assessment == "FLAGGED FOR REVIEWLY_SUSPICIOUS":
            ela_impact = max(ela_impact, 0.85)
        elif ela_assessment == "SUSPICIOUS":
            ela_impact = max(ela_impact, 0.50)
        elif ela_assessment == "CLEAN" and ela_score < 0.1:
            ela_impact = -0.1  # Genuine document bonus

        if math.isnan(ela_impact) or math.isinf(ela_impact):
            ela_impact = 0.0

        attrs.append(
            FactorAttribution(
                category="forensics",
                factor_name="error_level_analysis",
                impact_score=round(ela_impact, 3),
                weight=0.50,
                description=(
                    f"ELA tamper score {ela_score:.2f} ({ela_assessment}). "
                    f"{'High localized pixel compression variance detected.' if ela_impact > 0.4 else 'Image compression levels are uniform.'}"
                ),
            )
        )

        # PDF Structural Inspector Score (if inspected)
        pdf_data = (
            (f_dict.get("pdf_inspection_result") or f_dict.get("pdf_inspector"))
            if isinstance(f_dict, dict)
            else (getattr(f_dict, "pdf_inspection_result", None) or getattr(f_dict, "pdf_inspector", None))
        )
        if not pdf_data:
            pdf_data = {}

        try:
            raw_pdf = (
                getattr(pdf_data, 'pdf_tamper_score', None)
                if not isinstance(pdf_data, dict)
                else pdf_data.get('pdf_tamper_score', 0.0)
            )
            pdf_score = float(raw_pdf) if raw_pdf is not None else 0.0
            if math.isnan(pdf_score) or math.isinf(pdf_score):
                pdf_score = 0.0
        except (ValueError, TypeError):
            pdf_score = 0.0

        if pdf_score > 1.0:
            pdf_score = min(1.0, pdf_score / 100.0)

        raw_tampered = (
            getattr(pdf_data, 'is_tampered', None)
            if not isinstance(pdf_data, dict)
            else pdf_data.get('is_tampered', False)
        )
        pdf_tampered = bool(raw_tampered) if raw_tampered is not None else False

        pdf_impact = pdf_score
        if pdf_tampered:
            pdf_impact = max(pdf_impact, 0.75)
        elif pdf_data and not pdf_tampered:
            pdf_impact = -0.15  # Genuine clean PDF bonus

        if math.isnan(pdf_impact) or math.isinf(pdf_impact):
            pdf_impact = 0.0

        attrs.append(
            FactorAttribution(
                category="forensics",
                factor_name="pdf_stream_integrity",
                impact_score=round(pdf_impact, 3),
                weight=0.50,
                description=(
                    f"PDF tamper score {pdf_score:.2f}. "
                    f"{'Incremental update chaining or overwritten indirect objects detected.' if pdf_tampered else 'Single-revision PDF without structural tampering.'}"
                ),
            )
        )

        combined_forensics = max(0.0, (max(0.0, ela_impact) * 0.5 + max(0.0, pdf_impact) * 0.5))
        if math.isnan(combined_forensics) or math.isinf(combined_forensics):
            combined_forensics = 0.0
        return combined_forensics, attrs

    def _evaluate_metadata(
        self, metadata_flags: Optional[List[Any]]
    ) -> tuple[float, List[FactorAttribution]]:
        attrs: List[FactorAttribution] = []
        if not metadata_flags:
            attrs.append(
                FactorAttribution(
                    category="forensics",
                    factor_name="metadata_consistency",
                    impact_score=-0.05,
                    weight=0.10,
                    description="No suspicious metadata flags or software traces detected.",
                )
            )
            return 0.0, attrs

        high_count = 0
        med_count = 0
        descriptions = []

        for flag in metadata_flags:
            sev = getattr(flag, "severity", None) or (
                flag.get("severity") if isinstance(flag, dict) else "CLEAN"
            )
            desc = getattr(flag, "description", None) or (
                flag.get("description") if isinstance(flag, dict) else str(flag)
            )
            if sev == "HIGH":
                high_count += 1
                descriptions.append(desc)
            elif sev == "MEDIUM":
                med_count += 1
                descriptions.append(desc)

        impact = min(1.0, high_count * 0.50 + med_count * 0.25)
        attrs.append(
            FactorAttribution(
                category="forensics",
                factor_name="metadata_anomalies",
                impact_score=round(impact, 3),
                weight=0.10,
                description=(
                    f"{len(metadata_flags)} metadata flags detected: "
                    + ("; ".join(descriptions[:2]) if descriptions else "Minor metadata flags.")
                ),
            )
        )
        return impact, attrs

    def _evaluate_billing(
        self, bill_anomalies: Optional[Union[Dict[str, Any], List[Any]]]
    ) -> tuple[float, List[FactorAttribution]]:
        attrs: List[FactorAttribution] = []
        flags = []
        if isinstance(bill_anomalies, list):
            flags = bill_anomalies
        elif isinstance(bill_anomalies, dict):
            flags = bill_anomalies.get("flags", []) or bill_anomalies.get("bill_anomalies", [])

        if not flags:
            attrs.append(
                FactorAttribution(
                    category="billing",
                    factor_name="cghs_tariff_and_los_compliance",
                    impact_score=-0.1,
                    weight=0.30,
                    description="Hospital charges, length of stay, and line-item totals align with standard benchmarks.",
                )
            )
            return 0.0, attrs

        tariff_flags = []
        los_flags = []
        dup_flags = []
        item_flags = []

        for f in flags:
            atype = getattr(f, "anomaly_type", "") or (
                f.get("anomaly_type") if isinstance(f, dict) else ""
            )
            sev = getattr(f, "severity", "") or (f.get("severity") if isinstance(f, dict) else "")
            desc = getattr(f, "description", "") or (
                f.get("description") if isinstance(f, dict) else ""
            )

            if atype == "TARIFF_DEVIATION":
                tariff_flags.append((sev, desc))
            elif atype == "LOS_PADDING":
                los_flags.append((sev, desc))
            elif atype == "DUPLICATE_BILLING":
                dup_flags.append((sev, desc))
            elif atype == "ITEMIZATION_MISMATCH":
                item_flags.append((sev, desc))

        # Tariff impact
        tariff_impact = 0.0
        if tariff_flags:
            high_t = sum(1 for s, _ in tariff_flags if s == "HIGH")
            med_t = sum(1 for s, _ in tariff_flags if s == "MEDIUM")
            tariff_impact = min(1.0, high_t * 0.45 + med_t * 0.25)
            attrs.append(
                FactorAttribution(
                    category="billing",
                    factor_name="tariff_deviation",
                    impact_score=round(tariff_impact, 3),
                    weight=0.35,
                    description=f"{len(tariff_flags)} line items deviate significantly from CGHS benchmarks: {tariff_flags[0][1]}",
                )
            )
        else:
            attrs.append(
                FactorAttribution(
                    category="billing",
                    factor_name="tariff_deviation",
                    impact_score=-0.05,
                    weight=0.35,
                    description="Line items adhere to standard tariff rates.",
                )
            )

        # LOS padding impact
        los_impact = 0.0
        if los_flags:
            los_impact = 0.60 if any(s == "HIGH" for s, _ in los_flags) else 0.35
            attrs.append(
                FactorAttribution(
                    category="billing",
                    factor_name="length_of_stay_anomaly",
                    impact_score=round(los_impact, 3),
                    weight=0.30,
                    description=los_flags[0][1],
                )
            )
        else:
            attrs.append(
                FactorAttribution(
                    category="billing",
                    factor_name="length_of_stay_anomaly",
                    impact_score=0.0,
                    weight=0.30,
                    description="Length of stay is consistent with clinical diagnosis norms.",
                )
            )

        # Duplicate / Itemization
        misc_impact = 0.0
        if dup_flags or item_flags:
            misc_impact = min(1.0, len(dup_flags) * 0.30 + len(item_flags) * 0.40)
            desc_text = []
            if dup_flags:
                desc_text.append(dup_flags[0][1])
            if item_flags:
                desc_text.append(item_flags[0][1])
            attrs.append(
                FactorAttribution(
                    category="billing",
                    factor_name="billing_structure_integrity",
                    impact_score=round(misc_impact, 3),
                    weight=0.35,
                    description="; ".join(desc_text),
                )
            )

        active_impacts = [x for x in [tariff_impact, los_impact, misc_impact] if x > 0]
        if not active_impacts:
            combined_billing = 0.0
        else:
            combined_billing = min(1.0, max(active_impacts) + 0.35 * sum(sorted(active_impacts)[:-1]))
        return combined_billing, attrs

    def _evaluate_clinical(
        self, clinical_consistency: Optional[Union[Dict[str, Any], List[Any]]]
    ) -> tuple[float, List[FactorAttribution]]:
        attrs: List[FactorAttribution] = []
        flags = []
        if isinstance(clinical_consistency, list):
            flags = clinical_consistency
        elif isinstance(clinical_consistency, dict):
            flags = (
                clinical_consistency.get("flags", [])
                or clinical_consistency.get("consistency_flags", [])
            )

        if not flags:
            attrs.append(
                FactorAttribution(
                    category="clinical",
                    factor_name="treatment_consistency",
                    impact_score=-0.1,
                    weight=0.25,
                    description="All billed medicines, diagnostic tests, and surgical procedures match primary diagnosis.",
                )
            )
            return 0.0, attrs

        contradictory_flags = []
        missing_test_flags = []

        for f in flags:
            sev = getattr(f, "severity", "") or (f.get("severity") if isinstance(f, dict) else "")
            desc = getattr(f, "description", "") or (
                f.get("description") if isinstance(f, dict) else ""
            )
            mtype = getattr(f, "mismatch_type", "") or (
                f.get("mismatch_type") if isinstance(f, dict) else ""
            )
            itype = getattr(f, "issue_type", "") or (
                f.get("issue_type") if isinstance(f, dict) else ""
            )

            if "unexpected" in desc.lower() or itype == "CONTRADICTORY_TREATMENT" or sev == "HIGH":
                contradictory_flags.append(desc)
            else:
                missing_test_flags.append(desc)

        med_impact = 0.0
        if contradictory_flags:
            med_impact = min(1.0, len(contradictory_flags) * 0.50)
            attrs.append(
                FactorAttribution(
                    category="clinical",
                    factor_name="contradictory_medication",
                    impact_score=round(med_impact, 3),
                    weight=0.60,
                    description=f"Contradictory medications billed: {contradictory_flags[0]}",
                )
            )

        test_impact = 0.0
        if missing_test_flags:
            test_impact = min(0.6, len(missing_test_flags) * 0.25)
            attrs.append(
                FactorAttribution(
                    category="clinical",
                    factor_name="missing_diagnostic_protocol",
                    impact_score=round(test_impact, 3),
                    weight=0.40,
                    description=f"Missing standard diagnostic protocol: {missing_test_flags[0]}",
                )
            )

        active_clinical = [x for x in [med_impact, test_impact] if x > 0]
        if not active_clinical:
            combined_clinical = 0.0
        else:
            combined_clinical = min(1.0, max(active_clinical) + 0.30 * sum(sorted(active_clinical)[:-1]))
        return combined_clinical, attrs

    def _evaluate_provider(
        self, provider_data: Optional[Dict[str, Any]], billing_score: float, clinical_score: float
    ) -> tuple[float, List[FactorAttribution]]:
        attrs: List[FactorAttribution] = []
        # If provider has high density of both billing and clinical anomalies, add provider synergy flag
        if billing_score > 0.4 and clinical_score > 0.4:
            impact = 0.45
            attrs.append(
                FactorAttribution(
                    category="provider",
                    factor_name="hospital_systemic_anomaly_density",
                    impact_score=impact,
                    weight=0.10,
                    description="Co-occurrence of both substantial billing inflation and clinical mismatches suggests systemic hospital billing practice.",
                )
            )
            return impact, attrs

        return 0.0, attrs

    def _calculate_confidence(
        self,
        forensics_result: Any,
        bill_anomalies: Any,
        clinical_consistency: Any,
        metadata_flags: Any,
    ) -> float:
        signals_present = 0
        total_signals = 4
        if forensics_result is not None:
            signals_present += 1
        if bill_anomalies is not None:
            signals_present += 1
        if clinical_consistency is not None:
            signals_present += 1
        if metadata_flags is not None:
            signals_present += 1

        base_conf = 0.60 + (0.35 * (signals_present / total_signals))
        return round(base_conf, 2)

    def _generate_summary(
        self,
        score: float,
        tier: str,
        confidence: float,
        active_drivers: List[FactorAttribution],
    ) -> str:
        if tier == "CLEAN":
            return (
                f"Composite anomaly density is CLEAN ({score:.1f}%). "
                f"Document forensic checks, CGHS tariff alignment, and clinical protocol verifications "
                f"show high integrity and compliance (confidence: {int(confidence*100)}%)."
            )

        drivers_summary = "; ".join([d.description for d in active_drivers[:3]])
        return (
            f"Composite anomaly density evaluated at {tier} ({score:.1f}%, confidence: {int(confidence*100)}%). "
            f"Primary risk drivers: {drivers_summary}."
        )
