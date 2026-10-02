import axios from 'axios';
const api = axios.create({
  baseURL: import.meta.env?.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api',
  timeout: 10000,
});

// ==========================================
// Normalization Helpers
// ==========================================

export const normalizeStats = (backendStats) => {
  const s = backendStats || {};
  const totalRecovered = s.total_recovered_amount ?? s.total_amount_recovered ?? null;
  const pending = s.pending_analysis ?? s.pending_claims ?? 0;
  
  return {
    total_claims: s.total_claims ?? 0,
    pending_analysis: pending,
    pending_claims: pending, // Backward-compat for Dashboard.jsx:36
    mismatches_found: s.mismatches_found ?? 0,
    total_recovered_amount: totalRecovered,
    total_amount_recovered: totalRecovered, // Backward-compat for Dashboard.jsx:35
  };
};

export const normalizeClaims = (rawClaims) => {
  if (!Array.isArray(rawClaims)) return [];
  return rawClaims.filter(Boolean).map((claim) => {
    const safeClaim = claim || {};
    return {
      ...safeClaim,
      patient_name: safeClaim.patient_name ?? safeClaim.patient ?? null,
      patient: safeClaim.patient_name ?? safeClaim.patient ?? null,
      policy_number: safeClaim.policy_number ?? null,
      claim_number: safeClaim.claim_number ?? safeClaim.id ?? null,
      status: safeClaim.status ?? 'PENDING',
      docs: safeClaim.docs ?? safeClaim.documents_count ?? null,
      documents_count: safeClaim.docs ?? safeClaim.documents_count ?? null,
      impact: safeClaim.total_monetary_impact ?? safeClaim.impact ?? safeClaim.monetary_impact ?? null,
      monetary_impact: safeClaim.total_monetary_impact ?? safeClaim.impact ?? safeClaim.monetary_impact ?? null,
      created_at: safeClaim.created_at ?? safeClaim.updated_at ?? null,
      updated_at: safeClaim.updated_at ?? safeClaim.created_at ?? null,
      date: safeClaim.date ?? (safeClaim.created_at ? new Date(safeClaim.created_at).toLocaleDateString() : null),
    };
  });
};

export const normalizeAnalysisResult = (data, claimId = null) => {
  if (!data) return null;
  
  // Unwrap nested backend payload { analysis_run_id, status, result: { ... } }
  const core = (data && data.result) ? data.result : (data || {});
  
  return {
    ...core,
    claim_id: claimId ?? core.claim_id ?? data.claim_id ?? null,
    analysis_run_id: data.analysis_run_id ?? core.analysis_run_id ?? null,
    status: data.status ?? core.status ?? null,
    overall_status: core.overall_status ?? null,
    total_monetary_impact: core.total_monetary_impact ?? null,
    tier1_issues: core.tier1_issues ?? null,
    tier2_flags: core.tier2_flags ?? null,
    summary: core.summary ?? null,
    rule_verdicts: Array.isArray(core.rule_verdicts)
      ? core.rule_verdicts.map(v => ({ ...v }))
      : [],
    forensics: core.forensics ?? null,
    confidence_score: core.confidence_score ?? null,
    total_insurer_calculation: core.total_insurer_calculation ?? null,
    total_correct_calculation: core.total_correct_calculation ?? null,
  };
};

export const normalizeAppealDraft = (data) => {
  if (!data) return null;
  const text = typeof data.appeal_text === 'string'
    ? data.appeal_text
    : (data.appeal_letter || data.content || data.draft || null);
  if (!text || !text.trim()) return null;
  return {
    appeal_text: text,
    content: text, // Backward-compat for Analysis.jsx:63
    appeal_letter: text,
    regulatory_citations: data.regulatory_citations ?? [],
    monetary_impact: data.monetary_impact ?? null,
  };
};

// ==========================================
// API operations return backend data or surface the request error to the view.
// ==========================================

export const uploadDocument = async (file, documentType, claimId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  if (claimId) {
    formData.append('claim_id', claimId);
  }
  try {
    const response = await api.post('/upload', formData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const triggerAnalysis = async (claimId) => {
  try {
    const response = await api.post(`/analyze/${claimId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAnalysisStatus = async (claimId) => {
  try {
    const response = await api.get(`/analyze/${claimId}/status`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAnalysisResult = async (claimId) => {
  try {
    const response = await api.get(`/analyze/${claimId}/result`);
    return normalizeAnalysisResult(response.data, claimId);
  } catch (error) {
    throw error;
  }
};

export const getReport = async (claimId) => {
  try {
    const response = await api.get(`/reports/${claimId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getAppealDraft = async (claimId) => {
  try {
    const response = await api.get(`/reports/${claimId}/appeal`);
    return normalizeAppealDraft(response.data);
  } catch (error) {
    throw error;
  }
};

export const getAuditTrail = async (claimId) => {
  try {
    const response = await api.get(`/reports/${claimId}/audit-trail`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getDocuments = async (claimId) => {
  try {
    const response = await api.get(`/claims/${claimId}/documents`);
    return response.data;
  } catch (error) {
    return [];
  }
};

export const healthCheck = async () => {
  try {
    const response = await api.get('/health', { timeout: 3000 });
    return response.data;
  } catch (error) {
    return { status: 'offline', error: error.message };
  }
};

export const getClaims = async () => {
  try {
    const response = await api.get('/claims');
    return normalizeClaims(response.data);
  } catch (error) {
    throw error;
  }
};

export const getStats = async () => {
  try {
    const response = await api.get('/stats');
    return normalizeStats(response.data);
  } catch (error) {
    throw error;
  }
};

export default api;
