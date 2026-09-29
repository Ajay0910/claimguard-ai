amounts = {
    'ROOM': 22500,
    'NURSING': 5000,
    'CONSULTATION': 15000,
    'OT': 35000,
    'LAB': 25000,
    'PHARMACY': 15000,
    'MISC': 10000
}
room_limit = 4000
room_rate = 4500
deductible = 10000
copay = 0.1

for deduct_misc in [True, False]:
    for deduct_deductible in [True, False]:
        for apply_copay in [True, False]:
            for apply_prop_ded in [True, False]:
                for room_excess_applies in [True, False]:
                    for prop_items in [['NURSING', 'CONSULTATION'], ['ROOM', 'NURSING', 'CONSULTATION'], list(amounts.keys())]:
                        
                        expected = sum(amounts.values())
                        
                        if room_excess_applies:
                            expected -= 2500
                        if deduct_misc:
                            expected -= 10000
                        
                        if apply_prop_ded:
                            prop_base = sum(amounts[k] for k in prop_items)
                            expected -= prop_base * (1 - room_limit/room_rate)
                            
                        if deduct_deductible:
                            expected -= deductible
                            
                        if apply_copay:
                            expected -= expected * copay
                            
                        if abs(expected - 117954.60) < 1.0:
                            print("FOUND!", deduct_misc, deduct_deductible, apply_copay, apply_prop_ded, room_excess_applies, prop_items, expected)
