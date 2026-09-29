from ..schemas.hospital_bill import HospitalBill
from ..schemas.forensics_result import BillAnomalyFlag
from ..rules import get_val

# CGHS benchmark rates (2024)
CGHS_BENCHMARKS = {
    'ROOM': {'min': 2000, 'max': 5000, 'unit': 'per_day'},
    'NURSING': {'min': 500, 'max': 1500, 'unit': 'per_day'},
    'CONSULTATION': {'min': 500, 'max': 2000, 'unit': 'per_visit'},
    'LAB': {'min': 200, 'max': 5000, 'unit': 'per_test'},
    'RADIOLOGY': {'min': 1000, 'max': 15000, 'unit': 'per_test'},
    'OT': {'min': 10000, 'max': 50000, 'unit': 'per_procedure'},
    'PHARMACY': {'min': 500, 'max': 30000, 'unit': 'per_stay'},
    'CONSUMABLES': {'min': 500, 'max': 15000, 'unit': 'per_stay'},
}

# Average length of stay by diagnosis
TYPICAL_LOS = {
    'appendectomy': {'min': 2, 'max': 4},
    'cholecystectomy': {'min': 2, 'max': 5},
    'lscs': {'min': 3, 'max': 5},
    'caesarean': {'min': 3, 'max': 5},
    'knee replacement': {'min': 5, 'max': 8},
    'cataract': {'min': 1, 'max': 2},
    'angioplasty': {'min': 2, 'max': 4},
    'hernia': {'min': 1, 'max': 3},
    'hysterectomy': {'min': 3, 'max': 6},
}

class BillAnomalyDetector:
    def analyze(self, bill: HospitalBill) -> list[BillAnomalyFlag]:
        """
        Detect billing anomalies by comparing against CGHS benchmarks.
        """
        flags = []
        flags.extend(self._check_los_padding(bill))
        flags.extend(self._check_tariff_deviation(bill))
        flags.extend(self._check_duplicate_billing(bill))
        flags.extend(self._check_itemization(bill))
        return flags
    
    def _check_los_padding(self, bill: HospitalBill) -> list[BillAnomalyFlag]:
        flags = []
        diag = get_val(bill, 'diagnosis')
        los = get_val(bill, 'length_of_stay')
        if not diag or not los:
            return flags
            
        diag_lower = diag.lower()
        matched_diag = None
        for key in TYPICAL_LOS:
            if key in diag_lower:
                matched_diag = key
                break
                
        if matched_diag:
            typical_max = TYPICAL_LOS[matched_diag]['max']
            if los > typical_max * 1.5:
                flags.append(BillAnomalyFlag(
                    anomaly_type="LOS_PADDING",
                    description=f"Length of stay ({los} days) is significantly higher than typical max ({typical_max} days) for {matched_diag}",
                    severity="HIGH",
                    affected_items=[]
                ))
            elif los > typical_max:
                flags.append(BillAnomalyFlag(
                    anomaly_type="LOS_PADDING",
                    description=f"Length of stay ({los} days) is higher than typical max ({typical_max} days) for {matched_diag}",
                    severity="MEDIUM",
                    affected_items=[]
                ))
        return flags
    
    def _check_tariff_deviation(self, bill: HospitalBill) -> list[BillAnomalyFlag]:
        flags = []
        line_items = get_val(bill, 'line_items')
        if not line_items:
            return flags
            
        for item in line_items:
            cat_val = get_val(item, 'category')
            cat = cat_val.upper() if cat_val else ''
            if cat in CGHS_BENCHMARKS:
                bench_max = CGHS_BENCHMARKS[cat]['max']
                item_amount = get_val(item, 'amount', get_val(item, 'total', 0.0))
                item_desc = get_val(item, 'description', '')
                if item_amount > bench_max * 3:
                    flags.append(BillAnomalyFlag(
                        anomaly_type="TARIFF_DEVIATION",
                        description=f"Item '{item_desc}' amount (₹{item_amount:.2f}) is >3x CGHS benchmark max (₹{bench_max:.2f})",
                        severity="HIGH",
                        affected_items=[item_desc]
                    ))
                elif item_amount > bench_max * 2:
                    flags.append(BillAnomalyFlag(
                        anomaly_type="TARIFF_DEVIATION",
                        description=f"Item '{item_desc}' amount (₹{item_amount:.2f}) is >2x CGHS benchmark max (₹{bench_max:.2f})",
                        severity="MEDIUM",
                        affected_items=[item_desc]
                    ))
        return flags
    
    def _check_duplicate_billing(self, bill: HospitalBill) -> list[BillAnomalyFlag]:
        flags = []
        line_items = get_val(bill, 'line_items')
        if not line_items:
            return flags
            
        los = get_val(bill, 'length_of_stay', 1)
        if not los or los < 1:
            los = 1
            
        desc_counts = {}
        for item in line_items:
            desc = get_val(item, 'description', '').lower().strip()
            qty = get_val(item, 'quantity', 1)
            if desc in desc_counts:
                desc_counts[desc] += qty
            else:
                desc_counts[desc] = qty
                
        for desc, total_qty in desc_counts.items():
            if total_qty > (los * 5) and total_qty > 10:  # Adjust threshold based on LOS
                flags.append(BillAnomalyFlag(
                    anomaly_type="DUPLICATE_BILLING",
                    description=f"Excessive quantity ({total_qty}) for item: '{desc}' relative to length of stay ({los} days)",
                    severity="MEDIUM",
                    affected_items=[desc]
                ))
        return flags
    
    def _check_itemization(self, bill: HospitalBill) -> list[BillAnomalyFlag]:
        flags = []
        line_items = get_val(bill, 'line_items')
        net_payable = get_val(bill, 'net_payable')
        
        if not line_items or not net_payable or net_payable <= 0:
            return flags
            
        calculated_total = sum(get_val(item, 'amount', get_val(item, 'total', 0.0)) for item in line_items)
        if abs(calculated_total - net_payable) > 10.0:  # 10 INR tolerance
            flags.append(BillAnomalyFlag(
                anomaly_type="ITEMIZATION_MISMATCH",
                description=f"Sum of line items (₹{calculated_total:.2f}) does not match billed net payable (₹{net_payable:.2f})",
                severity="HIGH",
                affected_items=[]
            ))
        return flags
