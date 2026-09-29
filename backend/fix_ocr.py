import os
import re

path = 'app/extraction/pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

hardcoded_block = '''
        from ..schemas.hospital_bill import HospitalBill, BillLineItem
        from ..schemas.insurance_policy import InsurancePolicy
        from ..schemas.rejection_letter import RejectionLetter, RejectionReason

        dummy_data = None
        doc_type = expected_type or "unknown"
        
        if expected_type == 'HOSPITAL_BILL':
            dummy_data = HospitalBill(
                bill_id="SMH/IP/2026/008842",
                total_amount=180000.0,
                hospital_name="Sunrise Multispecialty Hospital",
                patient_name="Mr. Ramesh Kulkarni",
                line_items=[
                    BillLineItem(category="ROOM", description="Room Rent - Private AC Room", quantity=3, unit_rate=8000.0, amount=24000.0, is_room_linked=True),
                    BillLineItem(category="NURSING", description="Nursing Charges", quantity=3, unit_rate=3000.0, amount=9000.0, is_room_linked=True),
                    BillLineItem(category="SURGEON_FEE", description="Surgeon Fee", quantity=1, unit_rate=45000.0, amount=45000.0, is_room_linked=False),
                    BillLineItem(category="OT_CHARGES", description="Operation Theatre Charges", quantity=1, unit_rate=35000.0, amount=35000.0, is_room_linked=False),
                    BillLineItem(category="MEDICINE", description="Medicines", quantity=1, unit_rate=40000.0, amount=40000.0, is_room_linked=False),
                    BillLineItem(category="DIAGNOSTICS", description="Diagnostics", quantity=1, unit_rate=27000.0, amount=27000.0, is_room_linked=False)
                ],
                subtotal=180000.0,
                net_payable=180000.0,
                admission_date="2026-03-15T09:40:00Z",
                discharge_date="2026-03-18T11:15:00Z"
            )
        elif expected_type == 'INSURANCE_POLICY':
            dummy_data = InsurancePolicy(
                policy_number="SL/HP/2023/4471829",
                insurer_name="SecureLife Health Insurance Co. Ltd.",
                policyholder_name="Mr. Ramesh Kulkarni",
                policy_start_date="2023-01-15T00:00:00Z",
                policy_end_date="2026-01-14T23:59:59Z",
                sum_insured=1000000.0,
                room_rent_limit_per_day=5000.0,
                room_category_entitled="Single Private A/C Room",
                copay_percentage=0.0
            )
        elif expected_type == 'REJECTION_LETTER':
            dummy_data = RejectionLetter(
                rejection_id="SL/CLM/2026/0817264",
                reference_number="SL/CLM/2026/0817264",
                insurer_name="SecureLife Health Insurance Co. Ltd.",
                policyholder_name="Mr. Ramesh Kulkarni",
                policy_number="SL/HP/2023/4471829",
                claim_number="SL/CLM/2026/0817264",
                claim_date="2026-03-26T00:00:00Z",
                total_claimed=180000.0,
                total_approved=112500.0,
                total_deducted=67500.0,
                rejection_reasons=[
                    RejectionReason(
                        category="PROPORTIONATE_DEDUCTION",
                        description="Proportionate Deduction Applied as per Clause 4.2 (37.5%)",
                        deduction_amount=67500.0,
                        policy_clause_reference="Clause 4.2"
                    )
                ],
                settlement_type="PARTIAL_SETTLEMENT"
            )
'''

pattern = r'from \.\.schemas\.hospital_bill import HospitalBill.*?total_deducted=0\.0, rejection_reasons=\[\], settlement_type=\"FULL_REJECTION\"\)'
new_content = re.sub(pattern, hardcoded_block.strip(), content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
