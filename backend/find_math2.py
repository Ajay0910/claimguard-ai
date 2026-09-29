import itertools

amounts = [
    ('ROOM', 22500),
    ('NURSING', 5000),
    ('CONSULTATION', 15000),
    ('OT', 35000),
    ('LAB', 25000),
    ('PHARMACY', 15000),
    ('MISC', 10000)
]

target = 117954.60

for r in range(1, len(amounts) + 1):
    for combo in itertools.combinations(amounts, r):
        s = sum(v for k, v in combo)
        if abs(s - target) < 1.0:
            print("Subset sum:", combo)
        
        # apply copay
        if abs(s * 0.9 - target) < 1.0:
            print("Subset sum * 0.9:", combo)
            
        # apply 4000/4500
        prop = s * (4000/4500)
        if abs(prop - target) < 1.0:
            print("Subset sum * prop:", combo)
            
        if abs(prop * 0.9 - target) < 1.0:
            print("Subset sum * prop * 0.9:", combo)
            
        # What if it's 127500 - deductions?
        # deductions are some subset of amounts, plus maybe 2500, plus maybe deductible 10000
        pass

# Let's brute force total deductions
deduction_target = 127500 - target # 9545.40

# where can 9545.40 come from?
# 10606 * 0.9 = 9545.40
# Is there 10606 anywhere?
print("Deduction target:", deduction_target)
