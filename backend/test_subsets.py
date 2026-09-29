import itertools

items = {
    'Room': 22500,
    'Nursing': 5000,
    'Consultation': 15000,
    'OT': 35000,
    'Cath Lab': 25000,
    'Pharmacy': 15000,
    'Misc': 10000
}

target = 85914.00

for r in range(1, len(items)+1):
    for combo in itertools.combinations(items.items(), r):
        s = sum(v for k,v in combo)
        if abs(s - target) < 1.0:
            print("Found!", combo)
