/**
 * Realistic Mock Data for ClaimGuard AI
 * Strictly conforms to src/types/index.ts and backend Pydantic schemas.
 */

export const mockAuditor = {
  name: 'Dr. Aditi Sharma, CPC',
  title: 'Senior Medical Auditor',
  license: 'CPC-88219-IRDAI',
  department: 'Health Claim Integrity & Grievance',
  avatar_initials: 'AS',
};

export const mockTenant = {
  facility_name: 'St. Jude Multi-Specialty Hospital',
  tpa_desk: 'TPA & Commercial Claims Desk',
  accreditation: 'NABH Accredited Tertiary Care',
};

export const mockStats = {
  total_claims: 128,
  pending_analysis: 14,
  pending_claims: 14,
  mismatches_found: 42,
  total_recovered_amount: 1428500,
  total_amount_recovered: 1428500,
};

export const mockClaims = [
  {
    id: 'CLM-84920',
    patient_name: 'Ayush Sharma',
    patient: 'Ayush Sharma',
    policy_number: 'STAR-IND-99281',
    claim_number: 'CLM-84920',
    status: 'COMPLETED',
    docs: 3,
    documents_count: 3,
    impact: 42500,
    monetary_impact: 42500,
    created_at: '2026-09-15T09:30:00Z',
    updated_at: '2026-09-15T11:45:00Z',
    date: '15/09/2026',
    hospital: 'Apollo Hospitals, Bangalore',
    deduction_type: 'Proportionate Deduction Conflict',
    documents_status: { bill: true, policy: true, rejection: true },
  },
  {
    id: 'CLM-73812',
    patient_name: 'Priyadarshini Rao',
    patient: 'Priyadarshini Rao',
    policy_number: 'HDFC-ERGO-44120',
    claim_number: 'CLM-73812',
    status: 'COMPLETED',
    docs: 3,
    documents_count: 3,
    impact: 18000,
    monetary_impact: 18000,
    created_at: '2026-09-14T14:15:00Z',
    updated_at: '2026-09-14T16:00:00Z',
    date: '14/09/2026',
    hospital: 'Fortis Escorts Heart Institute',
    deduction_type: 'Moratorium Clause Contestation (Sec 45)',
    documents_status: { bill: true, policy: true, rejection: true },
  },
  {
    id: 'CLM-62941',
    patient_name: 'Rajesh Varma',
    patient: 'Rajesh Varma',
    policy_number: 'CARE-PLUS-11938',
    claim_number: 'CLM-62941',
    status: 'COMPLETED',
    docs: 3,
    documents_count: 3,
    impact: 65200,
    monetary_impact: 65200,
    created_at: '2026-09-13T10:00:00Z',
    updated_at: '2026-09-13T12:20:00Z',
    date: '13/09/2026',
    hospital: 'Max Super Speciality Hospital',
    deduction_type: 'Mental Health Parity Breach',
    documents_status: { bill: true, policy: true, rejection: true },
  },
  {
    id: 'CLM-51093',
    patient_name: 'Meera Patel',
    patient: 'Meera Patel',
    policy_number: 'NIVA-REASSURE-552',
    claim_number: 'CLM-51093',
    status: 'COMPLETED',
    docs: 3,
    documents_count: 3,
    impact: 0,
    monetary_impact: 0,
    created_at: '2026-09-12T16:45:00Z',
    updated_at: '2026-09-12T17:30:00Z',
    date: '12/09/2026',
    hospital: 'Manipal Hospital, Whitefield',
    deduction_type: 'Standard Co-pay Applied (Clean)',
    documents_status: { bill: true, policy: true, rejection: true },
  },
  {
    id: 'CLM-92340',
    patient_name: 'Sunita Krishnan',
    patient: 'Sunita Krishnan',
    policy_number: 'ICICI-HLT-77291',
    claim_number: 'CLM-92340',
    status: 'ANALYZING',
    docs: 3,
    documents_count: 3,
    impact: null,
    monetary_impact: null,
    created_at: '2026-09-17T14:00:00Z',
    updated_at: '2026-09-17T14:05:00Z',
    date: '17/09/2026',
    hospital: 'Medanta - The Medicity',
    deduction_type: 'Pipeline Running',
    documents_status: { bill: true, policy: true, rejection: true },
  },
  {
    id: 'CLM-41982',
    patient_name: 'Vikram Malhotra',
    patient: 'Vikram Malhotra',
    policy_number: 'NIA-MEDICLAIM-88',
    claim_number: 'CLM-41982',
    status: 'COMPLETED',
    docs: 3,
    documents_count: 3,
    impact: 27400,
    monetary_impact: 27400,
    created_at: '2026-09-11T11:20:00Z',
    updated_at: '2026-09-11T13:40:00Z',
    date: '11/09/2026',
    hospital: 'Lilavati Hospital, Mumbai',
    deduction_type: 'Tariff Deviation & ELA Alert',
    documents_status: { bill: true, policy: true, rejection: true },
  },
  {
    id: 'CLM-30219',
    patient_name: 'Ananya Sen',
    patient: 'Ananya Sen',
    policy_number: 'TATA-MED-33821',
    claim_number: 'CLM-30219',
    status: 'PENDING',
    docs: 2,
    documents_count: 2,
    impact: null,
    monetary_impact: null,
    created_at: '2026-09-17T08:00:00Z',
    updated_at: '2026-09-17T08:00:00Z',
    date: '17/09/2026',
    hospital: 'Narayana Multispeciality',
    deduction_type: 'Awaiting Rejection Letter',
    documents_status: { bill: true, policy: true, rejection: false },
  },
  {
    id: 'CLM-18475',
    patient_name: 'David D\'Souza',
    patient: 'David D\'Souza',
    policy_number: 'BAJAJ-HEALTH-991',
    claim_number: 'CLM-18475',
    status: 'FAILED',
    docs: 1,
    documents_count: 1,
    impact: null,
    monetary_impact: null,
    created_at: '2026-09-10T09:00:00Z',
    updated_at: '2026-09-10T09:12:00Z',
    date: '10/09/2026',
    hospital: 'Christian Medical College Vellore',
    deduction_type: 'OCR Resolution Below Threshold',
    documents_status: { bill: true, policy: false, rejection: false },
  },
];

export const mockAnalysisResult = {
  claim_id: 'CLM-84920',
  analysis_run_id: 'RUN-88410',
  status: 'COMPLETED',
  analysis_timestamp: '2026-09-15T11:45:00Z',
  documents_analyzed: [
    'apollo_hospital_bill_itemized.pdf',
    'star_health_optima_policy.pdf',
    'settlement_deduction_voucher.pdf'
  ],
  overall_status: 'MISMATCH_DETECTED',
  total_monetary_impact: 42500,
  tier1_issues: 2,
  tier2_flags: 1,
  confidence_score: 0.96,
  total_insurer_calculation: 68000,
  total_correct_calculation: 110500,
  summary: 'Insurer wrongfully applied proportionate deductions across fixed medical procedures (OT, Consultation, Pharmacy) in conflict of IRDAI Master Circular May 2024. Total recoverable underpayment is ₹42,500.00.',
  rule_verdicts: [
    {
      rule_name: 'Proportionate Deduction Audit (IRDAI May 2024)',
      rule_description: 'Validates that proportionate deduction is restricted strictly to room-rent linked expenses.',
      status: 'FAIL',
      confidence: 0.98,
      finding: 'Insurer reduced OT charges (₹35,000) and Consultation fees (₹15,000) by 40% due to room category upgrade. Under IRDAI Master Circular 2024, fixed medical fees cannot be scaled proportionately.',
      insurer_calculation: 30000,
      correct_calculation: 62000,
      monetary_impact: 32000,
      regulatory_citation: 'IRDAI Master Circular on Operations and Allied Matters May 2024 (Ref: IRDAI/HLT/REG/CIR/084/05/2024, Clause 12.3)',
      appeal_recommendation: 'Demand reimbursement of ₹32,000.00 wrongfully withheld on non-room medical expenses.',
    },
    {
      rule_name: 'Clause Timeline & Moratorium Period Protection',
      rule_description: 'Enforces statutory protection under Section 45 of Insurance Act against arbitrary pre-existing condition rejections.',
      status: 'FAIL',
      confidence: 0.95,
      finding: 'Insurer disallowed post-operative hypertension stabilization medication claiming pre-existing condition non-disclosure. Policy has been continuously active for 64 months, exceeding the 60-month moratorium window.',
      insurer_calculation: 0,
      correct_calculation: 10500,
      monetary_impact: 10500,
      regulatory_citation: 'Insurance Act 1938 Section 45 & IRDAI Health Insurance Regulations (Regulation 15 - 60-month Moratorium)',
      appeal_recommendation: 'Cite Section 45 immunity; insurer cannot contest policy after continuous 5-year coverage.',
    },
    {
      rule_name: 'Mental Health Parity Protection',
      rule_description: 'Verifies non-discrimination under Mental Healthcare Act 2017 Section 21(4).',
      status: 'PASS',
      confidence: 0.99,
      finding: 'No psychiatric or neurological parity deductions detected in settlement voucher.',
      insurer_calculation: 0,
      correct_calculation: 0,
      monetary_impact: 0,
      regulatory_citation: 'Section 21(4), Mental Healthcare Act 2017',
      appeal_recommendation: null,
    },
    {
      rule_name: 'Waiting Period Statutory Compliance',
      rule_description: 'Audits initial 30-day, 24-month specific ailment, and 48-month PED waiting periods.',
      status: 'PASS',
      confidence: 0.97,
      finding: 'Admission occurred in month 65 of coverage. All waiting periods satisfied.',
      insurer_calculation: 0,
      correct_calculation: 0,
      monetary_impact: 0,
      regulatory_citation: 'IRDAI Health Insurance Guidelines 2020 (Waiting Period Standardisation)',
      appeal_recommendation: null,
    },
  ],
  forensics: {
    claim_id: 'CLM-84920',
    ela_result: {
      tamper_score: 8.4,
      assessment: 'CLEAN',
      details: 'Error level compression gradient is uniform across all document layers. No digital clone stamping or splicing found.',
      suspicious_regions: [],
      heatmap_url: null,
    },
    metadata_flags: [
      {
        flag_type: 'VERIFIED_HARDWARE_SOURCE',
        field_name: 'Producer',
        expected_value: 'Hospital Multi-function Scanner',
        actual_value: 'Canon imageRUNNER ADVANCE C5550i',
        severity: 'LOW',
        description: 'Document originated from hospital scanner hardware; no editing tool tags detected.',
      }
    ],
    bill_anomalies: [
      {
        anomaly_type: 'TARIFF_DEVIATION',
        severity: 'MEDIUM',
        description: 'OT Consumable Pack charged at ₹14,500 vs CGHS Bengaluru benchmark rate of ₹8,200.',
        affected_items: ['Laparoscopy Consumable Kit', 'Disposable Trocar 12mm'],
        benchmark_value: 8200,
        actual_value: 14500,
      }
    ],
    consistency_flags: [],
    overall_risk: 'LOW',
    recommendation: 'Authenticity verified. Proceed with statutory grievance submission for the ₹42,500.00 underpayment.',
    disclaimer: 'Forensic integrity assessment generated via automated Error Level Analysis (ELA) and CGHS tariff benchmarking.',
  },
};

export const mockAppealDraft = {
  appeal_text: `To,
The Grievance Redressal Officer (GRO),
Star Health and Allied Insurance Company Limited,
Grievance Department, Chennai - 600034.

SUBJECT: FORMAL STATUTORY GRIEVANCE REGARDING UNLAWFUL CLAIM DEDUCTIONS
Reference: Claim ID: CLM-84920 | Policy No: STAR-IND-99281 | Patient: Ayush Sharma

Dear Sir/Madam,

We write on behalf of the policyholder, Mr. Ayush Sharma, regarding the partial settlement voucher issued on 14/09/2026 disallowing an aggregate sum of ₹42,500.00 against hospital bill net total ₹1,24,000.00.

Following automated forensic and statutory audit, we highlight the following non-compliant deductions:

1. CONFLICT OF IRDAI MASTER CIRCULAR ON PROPORTIONATE DEDUCTION:
Under IRDAI Master Circular on Operations and Allied Matters May 2024 (Ref: IRDAI/HLT/REG/CIR/084/05/2024, Clause 12.3), proportionate deduction on room category variation may ONLY be applied to associated room rent and nursing expenses. The insurer has unlawfully applied a 40% deduction to Operation Theatre charges (₹35,000) and Specialist Consultation fees (₹15,000), withholding ₹32,000.00 contrary to explicit statutory mandate.

2. CONFLICT OF SECTION 45 MORATORIUM PERIOD IMMUNITY:
The policy has been continuously active for 64 months since inception. Under Section 45 of the Insurance Act 1938 and Regulation 15 of IRDAI Health Insurance Regulations, no claim can be repudiated or contested for pre-existing non-disclosure after continuous 60 months of coverage. The deduction of ₹10,500.00 on this ground is void ab initio.

DEMAND FOR REIMBURSEMENT:
We formally demand the immediate release of the wrongfully withheld amount of ₹42,500.00 within 15 days of this notice, failing which this matter shall be escalated to the Insurance Ombudsman under Section 16 of the Insurance Ombudsman Rules, 2017.

Sincerely,
Dr. Aditi Sharma, CPC
Senior Medical Claims Auditor
St. Jude Multi-Specialty Hospital`,
  regulatory_citations: [
    'IRDAI Master Circular May 2024 (IRDAI/HLT/REG/CIR/084/05/2024, Clause 12.3)',
    'Section 45 of the Insurance Act 1938 (60-Month Moratorium Rule)',
    'Rule 16, Insurance Ombudsman Rules 2017',
  ],
  monetary_impact: 42500,
};

export const mockAuditTrail = {
  claim_id: 'CLM-84920',
  verified: true,
  audit_logs: [
    {
      id: 1,
      claim_id: 'CLM-84920',
      action: 'DOCUMENT_INGESTION',
      actor: 'Auditor: Dr. Aditi Sharma',
      details: { files: ['bill.pdf', 'policy.pdf', 'rejection.pdf'], sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' },
      previous_hash: '0000000000000000000000000000000000000000000000000000000000000000',
      entry_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      created_at: '2026-09-15T09:30:12Z',
    },
    {
      id: 2,
      claim_id: 'CLM-84920',
      action: 'VLM_EXTRACTION_COMPLETED',
      actor: 'ClaimGuard VLM Pipeline (claude-3-5-sonnet)',
      details: { hospital_bill_items: 24, policy_limits_identified: 6, rejection_reasons: 2 },
      previous_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      entry_hash: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
      created_at: '2026-09-15T09:31:05Z',
    },
    {
      id: 3,
      claim_id: 'CLM-84920',
      action: 'FORENSICS_AND_ELA_VERIFIED',
      actor: 'Forensic Engine v2.1',
      details: { tamper_score: 8.4, ela_assessment: 'CLEAN', cghs_anomalies: 1 },
      previous_hash: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
      entry_hash: 'ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d',
      created_at: '2026-09-15T09:31:42Z',
    },
    {
      id: 4,
      claim_id: 'CLM-84920',
      action: 'RULE_ENGINE_EVALUATION',
      actor: 'IRDAI Statutory Rules Evaluator',
      details: { rules_evaluated: 4, fail_count: 2, pass_count: 2, monetary_impact: 42500 },
      previous_hash: 'ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d',
      entry_hash: 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35',
      created_at: '2026-09-15T09:32:15Z',
    },
    {
      id: 5,
      claim_id: 'CLM-84920',
      action: 'AUDIT_REPORT_SEALED',
      actor: 'System Integrity Service',
      details: { status: 'MISMATCH_DETECTED', block_depth: 5, ledger_verified: true },
      previous_hash: 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35',
      entry_hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
      created_at: '2026-09-15T09:32:30Z',
    },
  ],
};
