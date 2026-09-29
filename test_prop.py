import json
from backend.tests.test_rules import get_base_bill, get_base_policy, get_base_rejection
from backend.app.schemas.hospital_bill import BillLineItem
from backend.app.rules.proportionate_deduction import check_proportionate_deduction

bill = get_base_bill()
bill.line_items = [
    BillLineItem(description="Room", category="ROOM", quantity=1, unit_rate=4000, amount=4000, is_room_linked=True)
]
policy = get_base_policy()
policy.room_rent_limit_per_day = 5000
rejection = get_base_rejection()
rejection.total_deducted = 0.0

verdict = check_proportionate_deduction(bill, policy, rejection)
print(verdict)
