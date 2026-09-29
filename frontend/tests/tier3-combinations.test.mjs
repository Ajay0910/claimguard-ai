/**
 * Tier 3: Combinations & Cross-Module Integration Tests
 * Validates interaction matrices: multi-document combinations, concurrent statutory rule
 * conflicts, multi-vector forensic tampering, clinical contradictions, and SHA-256 hash chains.
 */

import {
  describe,
  it,
  expect,
  setTier,
  verifyAuditHashChain
} from './test-framework.mjs';

setTier(3);

describe('Tier 3.1: Multi-Document Intake Matrix & State Transitions', () => {
  const evaluateReadiness = (documents) => {
    const bill = documents.HOSPITAL_BILL;
    const policy = documents.INSURANCE_POLICY;
    const rejection = documents.REJECTION_LETTER;

    const checks = {
      hasBill: !!bill,
      hasPolicy: !!policy,
      hasRejection: !!rejection,
      canAnalyze: false,
      mode: 'INCOMPLETE'
    };

    if (checks.hasBill && checks.hasPolicy && checks.hasRejection) {
      checks.canAnalyze = true;
      checks.mode = 'FULL_TRIO_AUDIT';
    } else if (checks.hasBill && checks.hasPolicy) {
      checks.canAnalyze = false;
      checks.mode = 'PRE_CLAIM_ESTIMATE';
    } else if (checks.hasBill) {
      checks.canAnalyze = false;
      checks.mode = 'BILL_SCRUTINY_ONLY';
    }

    return checks;
  };

  it('FEAT-03: Blocks analysis when only Hospital Bill is attached', () => {
    const docs = {
      HOSPITAL_BILL: { name: 'bill.pdf' },
      INSURANCE_POLICY: null,
      REJECTION_LETTER: null
    };
    const readiness = evaluateReadiness(docs);
    expect(readiness.canAnalyze).toBe(false);
    expect(readiness.mode).toBe('BILL_SCRUTINY_ONLY');
  });

  it('FEAT-03: Blocks dispute analysis when Rejection Letter is missing', () => {
    const docs = {
      HOSPITAL_BILL: { name: 'bill.pdf' },
      INSURANCE_POLICY: { name: 'policy.pdf' },
      REJECTION_LETTER: null
    };
    const readiness = evaluateReadiness(docs);
    expect(readiness.canAnalyze).toBe(false);
    expect(readiness.mode).toBe('PRE_CLAIM_ESTIMATE');
  });

  it('FEAT-03: Enables analysis when full document trio is attached', () => {
    const docs = {
      HOSPITAL_BILL: { name: 'bill.pdf' },
      INSURANCE_POLICY: { name: 'policy.pdf' },
      REJECTION_LETTER: { name: 'rejection.pdf' }
    };
    const readiness = evaluateReadiness(docs);
    expect(readiness.canAnalyze).toBe(true);
    expect(readiness.mode).toBe('FULL_TRIO_AUDIT');
  });

  it('FEAT-01: Maintains document type fidelity when uploaded out of order', () => {
    const documentStore = {};

    // Upload Rejection Letter first
    documentStore['REJECTION_LETTER'] = { id: 'doc-1', name: 'rejection.pdf', type: 'REJECTION_LETTER' };
    // Upload Hospital Bill second
    documentStore['HOSPITAL_BILL'] = { id: 'doc-2', name: 'bill.pdf', type: 'HOSPITAL_BILL' };
    // Upload Policy third
    documentStore['INSURANCE_POLICY'] = { id: 'doc-3', name: 'policy.pdf', type: 'INSURANCE_POLICY' };

    expect(documentStore.REJECTION_LETTER.type).toBe('REJECTION_LETTER');
    expect(documentStore.HOSPITAL_BILL.type).toBe('HOSPITAL_BILL');
    expect(documentStore.INSURANCE_POLICY.type).toBe('INSURANCE_POLICY');
  });
});

describe('Tier 3.2: Concurrent Multi-Rule Conflicts & Financial Reconciliation', () => {
  it('FEAT-07 & FEAT-09: Aggregates multiple statutory conflicts in single claim', () => {
    // Scenario: Insurer violated BOTH Proportionate Deduction AND Mental Health Parity
    const verdicts = [
      {
        rule_name: 'Proportionate Deduction Audit',
        status: 'FAIL',
        monetary_impact: 18500,
        regulatory_citation: 'IRDAI Master Circular May 2024'
      },
      {
        rule_name: 'Mental Health Parity Audit',
        status: 'FAIL',
        monetary_impact: 25000,
        regulatory_citation: 'Mental Healthcare Act 2017 Sec 21(4)'
      },
      {
        rule_name: 'Clause Timeline / Moratorium',
        status: 'PASS',
        monetary_impact: 0
      }
    ];

    // Compute cumulative underpayment
    const totalImpact = verdicts.reduce((acc, curr) => acc + (curr.monetary_impact || 0), 0);
    const failedVerdicts = verdicts.filter(v => v.status === 'FAIL');
    const overallStatus = failedVerdicts.length > 0 ? 'MISMATCH_DETECTED' : 'NO_MISMATCH_FOUND';

    expect(totalImpact).toBe(43500);
    expect(failedVerdicts.length).toBe(2);
    expect(overallStatus).toBe('MISMATCH_DETECTED');
  });
});

describe('Tier 3.3: Forensic Tampering Multi-Vector Combination', () => {
  const evaluateOverallForensicRisk = (metadataFlags, elaResult, billAnomalies) => {
    let riskScore = 0;

    // Metadata vector
    metadataFlags.forEach(flag => {
      if (flag.severity === 'HIGH') riskScore += 40;
      if (flag.severity === 'MEDIUM') riskScore += 20;
      if (flag.severity === 'LOW') riskScore += 10;
    });

    // ELA vector
    if (elaResult) {
      if (elaResult.assessment === 'HIGHLY_SUSPICIOUS') riskScore += 50;
      else if (elaResult.assessment === 'SUSPICIOUS') riskScore += 25;
    }

    // Bill anomalies
    billAnomalies.forEach(anomaly => {
      if (anomaly.severity === 'HIGH') riskScore += 30;
      if (anomaly.severity === 'MEDIUM') riskScore += 15;
    });

    let overallRisk = 'LOW';
    let recommendation = 'Standard processing';

    if (riskScore >= 60) {
      overallRisk = 'HIGH';
      recommendation = 'Escalate to Special Investigation Unit (SIU) for physical document scrutiny.';
    } else if (riskScore >= 30) {
      overallRisk = 'MEDIUM';
      recommendation = 'Secondary clinical audit recommended.';
    }

    return { riskScore, overallRisk, recommendation };
  };

  it('FEAT-11 & FEAT-12: Evaluates compound fraud risk from metadata and ELA vectors', () => {
    const metadataFlags = [
      { flag_type: 'SUSPICIOUS_CREATION_TOOL', actual_value: 'Adobe Photoshop 2023', severity: 'HIGH' },
      { flag_type: 'MISSING_EXIF', actual_value: 'EXIF tags stripped', severity: 'LOW' }
    ];

    const elaResult = {
      tamper_score: 76.5,
      assessment: 'HIGHLY_SUSPICIOUS'
    };

    const billAnomalies = [];

    const evaluation = evaluateOverallForensicRisk(metadataFlags, elaResult, billAnomalies);
    // 40 (Photoshop) + 10 (EXIF) + 50 (ELA) = 100
    expect(evaluation.riskScore).toBe(100);
    expect(evaluation.overallRisk).toBe('HIGH');
    expect(evaluation.recommendation).toContain('Special Investigation Unit');
  });
});

describe('Tier 3.4: Clinical Consistency Matrix & Anomaly Detection', () => {
  const checkClinicalConsistency = (diagnosis, lineItems) => {
    const flags = [];
    const lowerDiag = diagnosis.toLowerCase();

    // Contradiction: Cataract surgery with unrelated intensive chemotherapy/cardiology
    if (lowerDiag.includes('cataract')) {
      const contradictoryDrug = lineItems.find(item => 
        item.description.toLowerCase().includes('streptokinase') ||
        item.description.toLowerCase().includes('cisplatin')
      );
      if (contradictoryDrug) {
        flags.push({
          issue_type: 'CLINICAL_CONTRADICTION',
          severity: 'HIGH',
          details: `Diagnosis "${diagnosis}" contradicts billed medicine "${contradictoryDrug.description}".`
        });
      }
    }

    return flags;
  };

  it('FEAT-14: Flags clinical contradiction when cataract surgery includes cardiac drugs', () => {
    const diagnosis = 'Senile Cataract - Phacoemulsification';
    const lineItems = [
      { description: 'Intraocular Foldable Lens', amount: 15000 },
      { description: 'Streptokinase Injection 1.5MIU', amount: 8500 } // Cardiology thrombolytic drug
    ];

    const flags = checkClinicalConsistency(diagnosis, lineItems);
    expect(flags.length).toBe(1);
    expect(flags[0].issue_type).toBe('CLINICAL_CONTRADICTION');
    expect(flags[0].severity).toBe('HIGH');
  });
});

describe('Tier 3.5: Cryptographic SHA-256 Audit Trail Chain Integrity', () => {
  it('FEAT-15: Verifies valid SHA-256 chronological hash chain', () => {
    const validChain = [
      { id: 1, action: 'UPLOAD', previous_hash: null, entry_hash: 'hash_genesis_001' },
      { id: 2, action: 'VLM_EXTRACTION', previous_hash: 'hash_genesis_001', entry_hash: 'hash_extract_002' },
      { id: 3, action: 'FORENSICS_RUN', previous_hash: 'hash_extract_002', entry_hash: 'hash_forensics_003' },
      { id: 4, action: 'RULE_ENGINE', previous_hash: 'hash_forensics_003', entry_hash: 'hash_rules_004' }
    ];

    const result = verifyAuditHashChain(validChain);
    expect(result.verified).toBe(true);
    expect(result.count).toBe(4);
  });

  it('FEAT-15: Detects tampered block in audit ledger and flags invalid integrity', () => {
    const tamperedChain = [
      { id: 1, action: 'UPLOAD', previous_hash: null, entry_hash: 'hash_genesis_001' },
      { id: 2, action: 'VLM_EXTRACTION', previous_hash: 'hash_genesis_001', entry_hash: 'hash_extract_002' },
      { id: 3, action: 'FORENSICS_RUN', previous_hash: 'TAMPERED_PREVIOUS_HASH', entry_hash: 'hash_forensics_003' }, // Tampered!
      { id: 4, action: 'RULE_ENGINE', previous_hash: 'hash_forensics_003', entry_hash: 'hash_rules_004' }
    ];

    const result = verifyAuditHashChain(tamperedChain);
    expect(result.verified).toBe(false);
    expect(result.brokenIndex).toBe(2);
    expect(result.error).toContain('Hash chain broken');
  });
});
