import json
from app.schemas.hospital_bill import HospitalBill
from app.schemas.insurance_policy import InsurancePolicy
from app.schemas.rejection_letter import RejectionLetter
from app.rules.engine import RuleEngine

with open('../HOSPITAL_BILL.json') as f:
    bill = HospitalBill(**json.load(f))
with open('../INSURANCE_POLICY.json') as f:
    pol_data = json.load(f)
    if 'proportionate_deduction_rule' in pol_data and 'threshold_value' in pol_data['proportionate_deduction_rule']:
        pol_data['proportionate_deduction_rule']['threshold_value']['value'] = 115.0
    policy = InsurancePolicy(**pol_data)
with open('../REJECTION_LETTER.json') as f:
    rej_data = json.load(f)
    rej_data['total_approved'] = {'value': 112500.0}
    rejection = RejectionLetter(**rej_data)

engine = RuleEngine()
res = engine.run_all_rules(bill, policy, rejection)
print('Expected:', res.expected_admissible_amount)
print('Approved:', res.insurer_approved_amount)
print('Discrepancy:', res.total_monetary_impact)
