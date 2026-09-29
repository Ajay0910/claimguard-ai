from ..schemas.hospital_bill import HospitalBill
from ..schemas.forensics_result import ConsistencyFlag
from ..rules import get_val

# Mapping of diagnoses to expected medicine categories and tests
DIAGNOSIS_MEDICINE_MAP = {
    'appendectomy': {
        'expected_medicines': ['antibiotic', 'analgesic', 'antiemetic', 'proton pump inhibitor'],
        'expected_tests': ['cbc', 'blood count', 'ultrasound', 'ct scan', 'urinalysis'],
        'unexpected_medicines': ['insulin', 'antihypertensive', 'chemotherapy', 'immunosuppressant'],
    },
    'cholecystectomy': {
        'expected_medicines': ['antibiotic', 'analgesic', 'ursodeoxycholic', 'antiemetic'],
        'expected_tests': ['ultrasound', 'liver function', 'cbc', 'mrcp'],
        'unexpected_medicines': ['insulin', 'chemotherapy'],
    },
    'knee replacement': {
        'expected_medicines': ['anticoagulant', 'analgesic', 'antibiotic', 'calcium', 'iron'],
        'expected_tests': ['xray', 'x-ray', 'mri', 'cbc', 'coagulation', 'ecg'],
        'unexpected_medicines': ['chemotherapy', 'antiretroviral'],
    },
    'cataract': {
        'expected_medicines': ['eye drop', 'antibiotic', 'steroid', 'mydriatic'],
        'expected_tests': ['biometry', 'oct', 'tonometry', 'visual acuity'],
        'unexpected_medicines': ['chemotherapy', 'anticoagulant', 'insulin'],
    },
    'depression': {
        'expected_medicines': ['antidepressant', 'ssri', 'anxiolytic', 'sedative'],
        'expected_tests': ['thyroid', 'cbc', 'vitamin b12', 'vitamin d'],
        'unexpected_medicines': ['antibiotic', 'chemotherapy'],
    },
}

class ConsistencyChecker:
    def analyze(self, bill: HospitalBill) -> list[ConsistencyFlag]:
        """
        Cross-reference diagnosis against billed medicines and tests.
        """
        flags = []
        diag = get_val(bill, 'diagnosis')
        line_items = get_val(bill, 'line_items')
        
        if not diag or not line_items:
            return flags
            
        diag_lower = self._normalize(diag)
        matched_diag = None
        for key in DIAGNOSIS_MEDICINE_MAP:
            if key in diag_lower:
                matched_diag = key
                break
                
        if not matched_diag:
            return flags
            
        expected_meds = DIAGNOSIS_MEDICINE_MAP[matched_diag]['expected_medicines']
        expected_tests = DIAGNOSIS_MEDICINE_MAP[matched_diag]['expected_tests']
        unexpected_meds = DIAGNOSIS_MEDICINE_MAP[matched_diag]['unexpected_medicines']
        
        billed_items_text = " ".join([self._normalize(get_val(item, 'description', '')) for item in line_items])
        
        for unexp in unexpected_meds:
            if unexp in billed_items_text:
                flags.append(ConsistencyFlag(
                    issue_type="CONTRADICTORY_TREATMENT",
                    mismatch_type="DIAGNOSIS_MEDICINE",
                    description=f"Found unexpected treatment '{unexp}' for diagnosis '{matched_diag}'",
                    severity="HIGH",
                    details=f"Unexpected treatment: {unexp}"
                ))
                
        found_test = False
        for exp_test in expected_tests:
            if exp_test in billed_items_text:
                found_test = True
                break
                
        if not found_test and expected_tests:
            flags.append(ConsistencyFlag(
                mismatch_type="DIAGNOSIS_MEDICINE",
                description=f"Missing standard expected tests for {matched_diag} (e.g., {expected_tests[0]})",
                severity="LOW",
                details=f"Missing test: {expected_tests[0]}"
            ))
            
        return flags
    
    def _normalize(self, text: str) -> str:
        return text.lower().strip()
    
    def _fuzzy_match(self, text: str, keywords: list[str]) -> bool:
        normalized = self._normalize(text)
        return any(kw in normalized for kw in keywords)
