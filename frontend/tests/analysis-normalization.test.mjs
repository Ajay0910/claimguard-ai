import { describe, it, expect, setTier } from './test-framework.mjs';
import { normalizeAnalysisResult, normalizeAppealDraft, normalizeClaims, normalizeStats } from '../src/services/api.js';

setTier(1);

describe('Live API normalization preserves missing data', () => {
  it('does not synthesize a demo analysis when the API has no result', () => {
    expect(normalizeAnalysisResult(null, 'claim-real')).toBeNull();
  });

  it('preserves unavailable financial values without demo defaults', () => {
    const result = normalizeAnalysisResult({
      status: 'COMPLETED',
      result: {
        claim_id: 'claim-real',
        overall_status: 'EXTRACTION_FAILED',
        total_monetary_impact: null,
        expected_admissible_amount: null,
        summary: 'Extraction failed',
      },
    }, 'claim-real');

    expect(result.total_monetary_impact).toBeNull();
    expect(result.expected_admissible_amount).toBeNull();
    expect(result.rule_verdicts).toEqual([]);
    expect(result.overall_status).toBe('EXTRACTION_FAILED');
    expect(result.claim_id).toBe('claim-real');
  });

  it('does not synthesize demo appeal text when the API has no draft', () => {
    expect(normalizeAppealDraft(null)).toBeNull();
  });

  it('keeps an empty backend claims list empty', () => {
    expect(normalizeClaims([])).toEqual([]);
  });

  it('keeps unknown portfolio recovery totals unavailable instead of zero', () => {
    const normalized = normalizeStats({ total_recovered_amount: null });
    expect(normalized.total_recovered_amount).toBe(null);
  });
});
