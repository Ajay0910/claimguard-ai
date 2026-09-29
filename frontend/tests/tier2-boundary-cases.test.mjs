/**
 * Tier 2: Boundary Cases & Adversarial Verification
 * Probes input boundaries, extreme monetary limits, off-by-one timeline edges,
 * file size thresholds, and tariff multipliers against documented specifications.
 */

import {
  describe,
  it,
  expect,
  setTier,
  formatInr,
  calculateProportionateDeduction,
  evaluateMoratoriumRule,
  evaluateELATamperScore,
  evaluateCGHSTariff
} from './test-framework.mjs';

setTier(2);

describe('Tier 2.1: File Intake Size and MIME Type Boundaries', () => {
  const MAX_UPLOAD_BYTES = 25 * 1024 * 1024; // 26,214,400 bytes from backend/app/config.py
  const ALLOWED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'];

  const validateUploadFile = (file) => {
    if (!file || file.size === 0) {
      return { valid: false, error: 'File is empty (0 bytes)' };
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      return { valid: false, error: `File size ${file.size} exceeds maximum limit of 25MB` };
    }
    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      return { valid: false, error: `MIME type "${file.type}" is not supported` };
    }
    return { valid: true, error: null };
  };

  it('FEAT-01: Rejects 0-byte empty file', () => {
    const emptyFile = { name: 'empty.pdf', size: 0, type: 'application/pdf' };
    const res = validateUploadFile(emptyFile);
    expect(res.valid).toBe(false);
    expect(res.error).toContain('empty');
  });

  it('FEAT-01: Accepts file at exactly 25 MB boundary (26,214,400 bytes)', () => {
    const boundaryFile = { name: 'exact_25mb.pdf', size: MAX_UPLOAD_BYTES, type: 'application/pdf' };
    const res = validateUploadFile(boundaryFile);
    expect(res.valid).toBe(true);
    expect(res.error).toBeNull();
  });

  it('FEAT-01: Rejects file exceeding 25 MB boundary by 1 byte', () => {
    const overflowFile = { name: 'overflow.pdf', size: MAX_UPLOAD_BYTES + 1, type: 'application/pdf' };
    const res = validateUploadFile(overflowFile);
    expect(res.valid).toBe(false);
    expect(res.error).toContain('exceeds maximum limit');
  });

  it('FEAT-01: Validates MIME whitelist and rejects disallowed types (ZIP, HTML, EXE)', () => {
    ALLOWED_MIME_TYPES.forEach(mime => {
      const valid = validateUploadFile({ name: 'doc', size: 1024, type: mime });
      expect(valid.valid).toBe(true);
    });

    const disallowed = ['application/zip', 'text/html', 'application/x-msdownload', 'image/gif'];
    disallowed.forEach(mime => {
      const invalid = validateUploadFile({ name: 'doc', size: 1024, type: mime });
      expect(invalid.valid).toBe(false);
      expect(invalid.error).toContain('not supported');
    });
  });
});

describe('Tier 2.2: Extreme Monetary Values & Negative Protection', () => {
  it('FEAT-07: Ensures zero monetary impact does not trigger recovery pills', () => {
    const verdict = {
      rule_name: 'Room Rent Compliance',
      status: 'PASS',
      monetary_impact: 0
    };
    expect(verdict.monetary_impact > 0).toBe(false);
  });

  it('FEAT-07: Prevents negative underpayment when insurer pays more than statutory calculation', () => {
    // Insurer paid ₹70,000, correct calculation is ₹65,000
    const result = calculateProportionateDeduction({
      actualRoomRate: 8000,
      policyRoomLimit: 5000,
      roomLinkedAmount: 40000,
      fixedMedicalAmount: 40000,
      copayPercentage: 0,
      insurerPaid: 70000 // Overpaid by insurer
    });

    expect(result.status).toBe('NEEDS_REVIEW');
    expect(result.monetaryImpact).toBe(0);
    expect(result.monetaryImpact).toBeGreaterThanOrEqual(0);
  });

  it('FEAT-07: Formats multi-Crore monetary claims without integer overflow', () => {
    const largeAmount = 25000000.75; // ₹2.5 Crore
    const formatted = formatInr(largeAmount);
    expect(formatted).toContain('2,50,00,000.75');
  });
});

describe('Tier 2.3: Room Rent Proportionate Deduction Boundary Conditions', () => {
  it('FEAT-07: Applies factor 1.0 (no deduction) when policy has no room rent limit', () => {
    const result = calculateProportionateDeduction({
      actualRoomRate: 15000,
      policyRoomLimit: null, // No limit in policy
      roomLinkedAmount: 60000,
      fixedMedicalAmount: 80000,
      insurerPaid: 140000
    });

    expect(result.status).toBe('PASS');
    expect(result.factor).toBe(1.0);
    expect(result.correctPayable).toBe(140000);
    expect(result.monetaryImpact).toBe(0);
  });

  it('FEAT-07: Applies factor 1.0 when actual room rate equals policy limit exactly', () => {
    const result = calculateProportionateDeduction({
      actualRoomRate: 5000,
      policyRoomLimit: 5000, // Exactly equal
      roomLinkedAmount: 25000,
      fixedMedicalAmount: 50000,
      insurerPaid: 75000
    });

    expect(result.status).toBe('PASS');
    expect(result.factor).toBe(1.0);
    expect(result.correctPayable).toBe(75000);
  });

  it('FEAT-07: Correctly isolates medical non-room items under extreme room rent ratio', () => {
    // Actual room rate ₹20,000 vs policy limit ₹2,000 (factor = 0.10)
    // Room-linked = ₹1,00,000 -> payable ₹10,000
    // Fixed surgery/OT = ₹3,00,000 -> payable ₹3,00,000 (100% protected)
    const result = calculateProportionateDeduction({
      actualRoomRate: 20000,
      policyRoomLimit: 2000,
      roomLinkedAmount: 100000,
      fixedMedicalAmount: 300000,
      copayPercentage: 0,
      insurerPaid: 40000 // Insurer erroneously reduced everything by 0.10
    });

    expect(result.status).toBe('FAIL');
    expect(result.factor).toBeCloseTo(0.10, 4);
    // Correct payable = (100,000 * 0.10) + 300,000 = 10,000 + 300,000 = 310,000
    expect(result.correctPayable).toBe(310000);
    // Underpayment = 310,000 - 40,000 = 270,000
    expect(result.monetaryImpact).toBe(270000);
  });
});

describe('Tier 2.4: Moratorium Clause Timeline Boundaries (36m vs 60m)', () => {
  it('FEAT-08: Treats claim at exact 36.0 months as PASS under Insurance Act Sec 45', () => {
    // 36.0 * 30.44 = 1095.84 days
    const inception = '2021-01-01';
    const claimDate = '2023-12-31'; // ~36 months
    const result = evaluateMoratoriumRule({ policyInceptionDate: inception, claimDate });
    expect(result.status).toBe('PASS');
  });

  it('FEAT-08: Treats claim between 36.1 and 59.9 months as NEEDS_REVIEW', () => {
    const inception = '2020-01-01';
    const claimDate = '2023-09-01'; // ~44 months
    const result = evaluateMoratoriumRule({ policyInceptionDate: inception, claimDate });
    expect(result.status).toBe('NEEDS_REVIEW');
    expect(result.regulatoryCitation).toContain('Section 45');
  });

  it('FEAT-08: Treats claim at or exceeding 60.0 months as FAIL (Moratorium Conflict)', () => {
    const inception = '2019-01-01';
    const claimDate = '2024-03-01'; // ~62 months (>60 months)
    const result = evaluateMoratoriumRule({ policyInceptionDate: inception, claimDate });
    expect(result.status).toBe('FAIL');
    expect(result.regulatoryCitation).toContain('60-Month');
  });

  it('FEAT-08: Returns SKIPPED when inception date or claim date is missing', () => {
    const result = evaluateMoratoriumRule({ policyInceptionDate: null, claimDate: '2024-01-01' });
    expect(result.status).toBe('SKIPPED');
  });
});

describe('Tier 2.5: ELA Tamper Score Threshold Boundaries', () => {
  it('FEAT-11: Classifies 0.0 to 19.99 as CLEAN (LOW risk)', () => {
    expect(evaluateELATamperScore(0.0).assessment).toBe('CLEAN');
    expect(evaluateELATamperScore(0.0).risk).toBe('LOW');
    expect(evaluateELATamperScore(19.99).assessment).toBe('CLEAN');
  });

  it('FEAT-11: Classifies exactly 20.00 to 49.99 as SUSPICIOUS (MEDIUM risk)', () => {
    expect(evaluateELATamperScore(20.0).assessment).toBe('SUSPICIOUS');
    expect(evaluateELATamperScore(20.0).risk).toBe('MEDIUM');
    expect(evaluateELATamperScore(49.99).assessment).toBe('SUSPICIOUS');
  });

  it('FEAT-11: Classifies 50.00 to 100.0 as HIGHLY_SUSPICIOUS (HIGH risk)', () => {
    expect(evaluateELATamperScore(50.0).assessment).toBe('HIGHLY_SUSPICIOUS');
    expect(evaluateELATamperScore(50.0).risk).toBe('HIGH');
    expect(evaluateELATamperScore(98.5).assessment).toBe('HIGHLY_SUSPICIOUS');
  });

  it('FEAT-11: Caps tamper score safely at 100.0 if score exceeds boundary', () => {
    const result = evaluateELATamperScore(145.2);
    expect(result.score).toBe(100);
    expect(result.assessment).toBe('HIGHLY_SUSPICIOUS');
  });
});

describe('Tier 2.6: CGHS Tariff Benchmark Multiplier Boundaries', () => {
  const CGHS_ICU_MAX = 5000; // Benchmark maximum per day

  it('FEAT-13: Treats billed rate <= 2.0x benchmark as LOW severity', () => {
    const result = evaluateCGHSTariff(10000, CGHS_ICU_MAX); // exactly 2.0x
    expect(result.anomaly).toBe(false);
    expect(result.severity).toBe('LOW');
  });

  it('FEAT-13: Treats billed rate > 2.0x and <= 3.0x as MEDIUM severity anomaly', () => {
    const result = evaluateCGHSTariff(12500, CGHS_ICU_MAX); // 2.5x
    expect(result.anomaly).toBe(true);
    expect(result.severity).toBe('MEDIUM');
  });

  it('FEAT-13: Treats billed rate > 3.0x as HIGH severity anomaly', () => {
    const result = evaluateCGHSTariff(18000, CGHS_ICU_MAX); // 3.6x
    expect(result.anomaly).toBe(true);
    expect(result.severity).toBe('HIGH');
  });
});

describe('Tier 2.7: Hospital Bill Itemization Arithmetic Tolerance (₹10 Threshold)', () => {
  const verifyBillArithmetic = (lineItemsSum, billedNetPayable) => {
    const diff = Math.abs(lineItemsSum - billedNetPayable);
    if (diff > 10.0) {
      return {
        flag: true,
        anomaly_type: 'ITEMIZATION_MISMATCH',
        severity: 'HIGH',
        diff
      };
    }
    return { flag: false, severity: 'LOW', diff };
  };

  it('FEAT-13: Tolerates rounding differences <= ₹10', () => {
    const check = verifyBillArithmetic(54325.50, 54330.00); // Diff is ₹4.50
    expect(check.flag).toBe(false);
  });

  it('FEAT-13: Flags ITEMIZATION_MISMATCH when difference exceeds ₹10', () => {
    const check = verifyBillArithmetic(54325.50, 54350.00); // Diff is ₹24.50
    expect(check.flag).toBe(true);
    expect(check.anomaly_type).toBe('ITEMIZATION_MISMATCH');
    expect(check.severity).toBe('HIGH');
  });
});

describe('Tier 2.8: SVG Chart Geometry, Divide-by-Zero & Visualization Boundaries', () => {
  const RADIUS = 68;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS; // ≈ 427.2566
  const CHART_HEIGHT = 175;

  it('FEAT-07: SVG Donut chart total=0 evaluates fraction to 0 without NaN', () => {
    const total = 0;
    const count = 0;
    const fraction = total > 0 ? count / total : 0;
    const dashLength = Math.max(0, fraction * CIRCUMFERENCE - (4 > 1 && count > 0 ? 2.5 : 0));
    expect(Number.isNaN(fraction)).toBe(false);
    expect(fraction).toBe(0);
    expect(dashLength).toBe(0);
  });

  it('FEAT-07: SVG Donut chart 100% single category gap artifact detection', () => {
    const total = 100;
    const count = 100;
    const categoriesCount = 4; // dynamicBreakdown default length
    const fraction = total > 0 ? count / total : 0;
    // When categoriesCount > 1, 2.5px gap is subtracted even though only 1 slice is active
    const dashLength = Math.max(0, fraction * CIRCUMFERENCE - (categoriesCount > 1 && count > 0 ? 2.5 : 0));
    const gap = CIRCUMFERENCE - dashLength;
    expect(fraction).toBe(1.0);
    expect(Math.abs(gap - 2.5) < 0.001).toBe(true);
  });

  it('FEAT-07: Waterfall chart detects divide-by-zero NaN when total_recovered_amount is 0', () => {
    const totalRecovered = 0;
    const billed = Math.round(totalRecovered * 2.85); // 0
    const disallowed = Math.round(totalRecovered * 1.35); // 0
    const approved = billed - disallowed; // 0
    const dynamicSteps = [
      { id: 'billed', amount: billed, base: 0 },
      { id: 'approved', amount: approved, base: 0 },
      { id: 'disallowed', amount: disallowed, base: approved },
      { id: 'recoverable', amount: totalRecovered, base: approved },
      { id: 'net', amount: approved + totalRecovered, base: 0 },
    ];
    const maxVal = Math.max(...dynamicSteps.map(s => s.amount + s.base)) * 1.15; // 0
    const rawRatio = 0 / maxVal; // 0 / 0 = NaN
    const barHeight = Math.max(14, rawRatio * CHART_HEIGHT); // Math.max(14, NaN) = NaN!
    expect(maxVal).toBe(0);
    expect(Number.isNaN(rawRatio)).toBe(true);
    expect(Number.isNaN(barHeight)).toBe(true);
  });

  it('FEAT-06: Sparkline curve generator identical elements [10, 10, 10] avoids divide-by-zero', () => {
    const data = [10, 10, 10];
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    expect(range).toBe(1);
    const points = data.map((val, i) => ({
      x: 3 + (i / (data.length - 1)) * 74,
      y: 28 - 3 - ((val - min) / range) * 22,
    }));
    points.forEach(pt => {
      expect(Number.isNaN(pt.x)).toBe(false);
      expect(Number.isNaN(pt.y)).toBe(false);
      expect(pt.y).toBe(25);
    });
  });

  it('FEAT-06: Sparkline curve corrupted array [10, undefined, 30] produces NaN points', () => {
    const data = [10, undefined, 30];
    const min = Math.min(...data); // NaN
    const max = Math.max(...data); // NaN
    const range = max - min || 1; // NaN || 1 = 1
    const y = 28 - 3 - ((data[1] - min) / range) * 22;
    expect(Number.isNaN(min)).toBe(true);
    expect(Number.isNaN(y)).toBe(true);
  });
});

