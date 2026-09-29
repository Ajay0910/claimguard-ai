# HOSPITAL_BILL.json amounts
room = 44500
nursing = 9000
consultation = 90000
ot = 38000
lab = 22000
pharmacy = 48650
consumables = 36800
misc = 3500

total_bill = 292450

room_limit = 7500
actual_rate = 8900
room_excess = 7000

prop_ded_pct = 1 - (room_limit/actual_rate) # 1400/8900

# Try to find exactly 47954.60
target = 47954.60

print(total_bill * prop_ded_pct)
print((room + nursing + consultation) * prop_ded_pct)
print((nursing + consultation) * prop_ded_pct)

# What if 47954.60 is the Discrepancy, and Insurer Approved = 112500?
expected = 112500 + 47954.60 # 160454.60
print("Expected:", expected)

# Deductions needed
deductions = total_bill - expected
print("Deductions needed:", deductions) # 131995.40

# Is there any combo of deductions that equals 131995.40?
# Maybe 42500 (Pre-existing) is deducted!
print("Deductions minus 42500:", deductions - 42500) # 89495.40
# Deductible 15000
print("Minus deductible 15000:", deductions - 42500 - 15000) # 74495.40

