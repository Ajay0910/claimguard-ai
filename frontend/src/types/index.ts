// ==========================================
// 1. Core Claim & Document Models
// ==========================================

export type ClaimStatus = 
  | 'QUEUED'
  | 'PENDING' 
  | 'EXTRACTING' 
  | 'ANALYZING' 
  | 'REVIEW_RECOMMENDED'
  | 'COMPLETED' 
  | 'FAILED';

export type DocumentType = 
  | 'HOSPITAL_BILL' 
  | 'INSURANCE_POLICY' 
  | 'REJECTION_LETTER';

export interface DocumentRecord {
  id: string;
  claim_id?: string;
  document_type: DocumentType;
  filename: string;
  file_path: string;
  content_type?: string;
  file_size_bytes?: number;
  created_at: string;
  extracted_data?: HospitalBill | InsurancePolicy | RejectionLetter | null;
  extraction_confidence?: number;
  extraction_method?: 'vlm' | 'ocr' | 'none';
}

export interface Claim {
  id: string;
  patient_name: string;
  patient?: string;
  policy_number?: string | null;
  claim_number?: string | null;
  status: ClaimStatus;
  created_at: string;
  updated_at: string;
  date?: string;
  documents_count?: number;
  docs?: number;
  monetary_impact?: number;
  impact?: number;
  hospital?: string;
  deduction_type?: string;
  documents_status?: {
    bill: boolean;
    policy: boolean;
    rejection: boolean;
  };
}

// ==========================================
// 2. Extracted Hospital Bill
// ==========================================

export type BillCategory = 
  | 'ROOM' 
  | 'NURSING' 
  | 'CONSULTATION' 
  | 'LAB' 
  | 'RADIOLOGY' 
  | 'OT' 
  | 'PHARMACY' 
  | 'CONSUMABLES' 
  | 'MISCELLANEOUS';

export interface BillLineItem {
  item_code?: string | null;
  description: string;
  category: BillCategory;
  quantity: number;
  unit_rate: number;
  amount: number;
  total?: number;
  is_room_linked: boolean;
}

export interface HospitalBill {
  bill_id?: string | null;
  total_amount: number;
  hospital_name: string;
  hospital_address?: string | null;
  gstin?: string | null;
  uhid?: string | null;
  patient_name: string;
  patient_age?: number | null;
  patient_gender?: string | null;
  admission_date?: string | null;
  discharge_date?: string | null;
  doctor_name?: string | null;
  ward_type?: string | null;
  bed_number?: string | null;
  tpa_or_insurer?: string | null;
  diagnosis?: string | null;
  line_items: BillLineItem[];
  subtotal: number;
  tax_amount: number;
  discount: number;
  net_payable: number;
  arithmetic_verified: boolean;
  extraction_confidence: number;
  room_charges_per_day?: number | null;
  length_of_stay?: number | null;
}

// ==========================================
// 3. Extracted Insurance Policy
// ==========================================

export interface WaitingPeriodConfig {
  category: 'INITIAL' | 'SPECIFIC_DISEASE' | 'PED';
  duration_days: number;
  applicable_conditions: string[];
}

export interface SubLimit {
  category: string;
  max_amount?: number | null;
  max_percentage?: number | null;
  description: string;
}

export interface InsurancePolicy {
  policy_number: string;
  insurer_name: string;
  policyholder_name: string;
  policy_holder_name?: string | null;
  inception_date?: string | null;
  original_inception_date?: string | null;
  policy_start_date: string;
  policy_end_date: string;
  sum_insured: number;
  room_rent_limit_per_day?: number | null;
  room_category_entitled?: string | null;
  copay_percentage: number;
  deductible: number;
  waiting_periods: WaitingPeriodConfig[];
  sub_limits: SubLimit[];
  covers_mental_health: boolean;
  covers_maternity: boolean;
  moratorium_period_months: number;
  exclusions: string[];
}

// ==========================================
// 4. Extracted Rejection Letter
// ==========================================

export type RejectionCategory = 
  | 'PROPORTIONATE_DEDUCTION' 
  | 'WAITING_PERIOD' 
  | 'PRE_EXISTING' 
  | 'EXCLUSION' 
  | 'DOCUMENT_INCOMPLETE' 
  | 'MENTAL_HEALTH' 
  | 'OTHER';

export interface RejectionReason {
  code: string;
  description: string;
  details?: string | null;
  clause_cited?: string | null;
  category: RejectionCategory;
}

export interface RejectionLetter {
  rejection_id?: string | null;
  reference_number: string;
  insurer_name: string;
  tpa_name?: string | null;
  policyholder_name: string;
  policy_number: string;
  claim_number: string;
  claim_date: string;
  total_claimed: number;
  total_approved: number;
  approved_amount?: number;
  total_deducted: number;
  rejection_reasons: RejectionReason[];
  reasons?: RejectionReason[];
  settlement_type: 'FULL_REJECTION' | 'PARTIAL_SETTLEMENT' | 'FULL_SETTLEMENT';
  remarks?: string | null;
  extraction_confidence: number;
  deduction_percentage?: number;
}

// ==========================================
// 5. Rule Engine & Verdicts
// ==========================================

export type VerdictStatus = 
  | 'PASS' 
  | 'FAIL' 
  | 'SKIPPED' 
  | 'NEEDS_REVIEW' 
  | 'INSUFFICIENT_EVIDENCE'
  | 'CONFLICT'
  | 'BLOCKED'
  | 'WARNING';

export interface RuleVerdict {
  rule_name: string;
  rule_description: string;
  status: VerdictStatus;
  confidence: number;
  finding: string;
  insurer_calculation?: number | null;
  correct_calculation?: number | null;
  monetary_impact?: number | null;
  regulatory_citation?: string | null;
  appeal_recommendation?: string | null;
}

export type OverallStatus = 
  | 'NO_MISMATCH_FOUND' 
  | 'MISMATCH_DETECTED' 
  | 'REVIEW_RECOMMENDED' 
  | 'EXTRACTION_FAILED'
  | 'BLOCKED'
  | 'INSUFFICIENT_EVIDENCE';

export interface AnalysisResult {
  claim_id: string;
  analysis_timestamp: string;
  documents_analyzed: string[];
  overall_status: OverallStatus;
  rule_verdicts: RuleVerdict[];
  total_monetary_impact: number;
  tier1_issues: number;
  tier2_flags: number;
  summary: string;
  forensics?: ForensicsResult | null;
  confidence_score?: number;
  total_insurer_calculation?: number;
  total_correct_calculation?: number;
  analysis_run_id?: string;
  status?: string;
}

// ==========================================
// 6. Forensics Models
// ==========================================

export type ELAAssessment = 'CLEAN' | 'SUSPICIOUS' | 'HIGHLY_SUSPICIOUS' | 'NOT_ANALYZED';

export interface ELAResult {
  tamper_score: number;
  suspicious_regions: Array<{ x?: number; y?: number; width?: number; height?: number; area?: number }>;
  heatmap_path?: string | null;
  heatmap_url?: string | null;
  details: string;
  assessment: ELAAssessment;
}

export interface MetadataFlag {
  flag_type: string;
  field_name: string;
  expected_value?: string | null;
  actual_value: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
}

export interface BillAnomalyFlag {
  anomaly_type: 'LOS_PADDING' | 'TARIFF_DEVIATION' | 'DUPLICATE_BILLING' | 'ITEMIZATION_MISMATCH';
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  affected_items: string[];
  benchmark_value?: number | null;
  actual_value?: number | null;
}

export interface ConsistencyFlag {
  issue_type: string;
  mismatch_type?: 'DIAGNOSIS_MEDICINE' | 'DIAGNOSIS_TEST' | 'PROCEDURE_BILLING' | null;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  details: string;
}

export interface ForensicsResult {
  claim_id: string;
  ela_result?: ELAResult | null;
  metadata_flags: MetadataFlag[];
  bill_anomalies: BillAnomalyFlag[];
  bill_anomaly_flags?: BillAnomalyFlag[];
  consistency_flags: ConsistencyFlag[];
  overall_risk: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendation: string;
  disclaimer: string;
}

// ==========================================
// 7. Audit Trail, Stats & App Shell
// ==========================================

export interface AuditLogEntry {
  id: number;
  claim_id?: string;
  action: string;
  actor: string;
  details: Record<string, any>;
  previous_hash?: string | null;
  entry_hash: string;
  created_at?: string;
}

export interface AuditTrailResponse {
  claim_id: string;
  verified: boolean;
  audit_logs: AuditLogEntry[];
}

export interface AppealDraftResponse {
  appeal_text: string;
  regulatory_citations: string[];
  monetary_impact: number;
  content?: string;
  appeal_letter?: string;
}

export interface DashboardStats {
  total_claims: number;
  pending_analysis: number;
  pending_claims?: number;
  mismatches_found: number;
  total_recovered_amount: number;
  total_amount_recovered?: number;
}

export interface AuditorProfile {
  name: string;
  title: string;
  license: string;
  department: string;
  avatar_initials: string;
}

export interface TenantContext {
  facility_name: string;
  tpa_desk: string;
  accreditation: string;
}
