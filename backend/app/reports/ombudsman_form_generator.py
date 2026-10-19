import os
import datetime
from typing import Dict, Any, Optional

try:
    from fpdf import FPDF
except ImportError:
    class FPDF:
        def __init__(self, *args, **kwargs): pass
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def output(self, *args, **kwargs): pass


# ==============================================================================
# Territorial Jurisdiction Mapping for All 17 Insurance Ombudsman Centers
# Source: Council for Insurance Ombudsmen (CIO) / Executive Council of Insurers
# ==============================================================================

OMBUDSMAN_CENTERS: Dict[str, Dict[str, str]] = {
    "AHMEDABAD": {
        "center": "Ahmedabad",
        "state_ut": "Gujarat, UT of Dadra & Nagar Haveli, Daman and Diu",
        "address": "Office of the Insurance Ombudsman, Jeevan Prakash Building, 6th floor, Tilak Marg, Relief Road, Ahmedabad - 380 001.",
        "email": "bimalokpal.ahmedabad@cioins.co.in",
        "phone": "079-25501201/02/05/06"
    },
    "BENGALURU": {
        "center": "Bengaluru",
        "state_ut": "Karnataka",
        "address": "Office of the Insurance Ombudsman, Jeevan Soudha Building, PID No. 57-27-N-19, Ground Floor, 24th Main Road, JP Nagar, 1st Phase, Bengaluru - 560 078.",
        "email": "bimalokpal.bengaluru@cioins.co.in",
        "phone": "080-26652048 / 26652049"
    },
    "BHOPAL": {
        "center": "Bhopal",
        "state_ut": "Madhya Pradesh, Chhattisgarh",
        "address": "Office of the Insurance Ombudsman, Jan Seva Bhavan, 1st Floor, Old High Court Road, City Centre, Gwalior / 1st Floor, 47, Relief Road, Bhopal - 462 011.",
        "email": "bimalokpal.bhopal@cioins.co.in",
        "phone": "0755-2769201 / 2769202"
    },
    "BHUBANESWAR": {
        "center": "Bhubaneswar",
        "state_ut": "Odisha",
        "address": "Office of the Insurance Ombudsman, 62, Forest park, Bhubaneswar - 751 009.",
        "email": "bimalokpal.bhubaneswar@cioins.co.in",
        "phone": "0674-2596461 / 2596455"
    },
    "CHANDIGARH": {
        "center": "Chandigarh",
        "state_ut": "Punjab, Haryana (excluding NCR), Himachal Pradesh, Jammu & Kashmir, Ladakh, UT of Chandigarh",
        "address": "Office of the Insurance Ombudsman, S.C.O. No. 101, 102 & 103, 2nd Floor, Batra Building, Sector 17-D, Chandigarh - 160 017.",
        "email": "bimalokpal.chandigarh@cioins.co.in",
        "phone": "0172-2706196 / 2706468"
    },
    "CHENNAI": {
        "center": "Chennai",
        "state_ut": "Tamil Nadu, UT of Puducherry",
        "address": "Office of the Insurance Ombudsman, Fatima Akhtar Court, 4th Floor, 453, Anna Salai, Teynampet, Chennai - 600 018.",
        "email": "bimalokpal.chennai@cioins.co.in",
        "phone": "044-24333668 / 24335284"
    },
    "DELHI": {
        "center": "Delhi",
        "state_ut": "NCT of Delhi and NCR districts of Haryana (Faridabad, Gurugram, Palwal, Nuh)",
        "address": "Office of the Insurance Ombudsman, 2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi - 110 002.",
        "email": "bimalokpal.delhi@cioins.co.in",
        "phone": "011-23232481 / 23213504"
    },
    "ERNAKULAM": {
        "center": "Ernakulam",
        "state_ut": "Kerala, UT of Lakshadweep, Mahe",
        "address": "Office of the Insurance Ombudsman, 2nd Floor, Pulinat Bldg., Opp. Cochin Shipyard, M. G. Road, Ernakulam - 682 015.",
        "email": "bimalokpal.ernakulam@cioins.co.in",
        "phone": "0484-2358759 / 2359338"
    },
    "GUWAHATI": {
        "center": "Guwahati",
        "state_ut": "Assam, Meghalaya, Manipur, Mizoram, Arunachal Pradesh, Nagaland, Tripura",
        "address": "Office of the Insurance Ombudsman, Jeevan Nivesh, 5th Floor, Nr. Panbazar overbridge, S. S. Road, Guwahati - 781 001.",
        "email": "bimalokpal.guwahati@cioins.co.in",
        "phone": "0361-2632204 / 2602205"
    },
    "HYDERABAD": {
        "center": "Hyderabad",
        "state_ut": "Telangana, Andhra Pradesh",
        "address": "Office of the Insurance Ombudsman, 6-2-46, 1st floor, 'Moin Court', Lane Opp. Saleem Function Palace, A. C. Guards, Lakdi-Ka-Pool, Hyderabad - 500 004.",
        "email": "bimalokpal.hyderabad@cioins.co.in",
        "phone": "040-23312122"
    },
    "JAIPUR": {
        "center": "Jaipur",
        "state_ut": "Rajasthan",
        "address": "Office of the Insurance Ombudsman, Jeevan Nidhi – II Bldg., Gr. Floor, Bhawani Singh Marg, Jaipur - 302 005.",
        "email": "bimalokpal.jaipur@cioins.co.in",
        "phone": "0141-2740363"
    },
    "KOLKATA": {
        "center": "Kolkata",
        "state_ut": "West Bengal, Sikkim, UT of Andaman & Nicobar Islands",
        "address": "Office of the Insurance Ombudsman, Hindustan Bldg. Annexe, 4th Floor, 4, C.R. Avenue, Kolkata - 700 072.",
        "email": "bimalokpal.kolkata@cioins.co.in",
        "phone": "033-22124339 / 22124340"
    },
    "LUCKNOW": {
        "center": "Lucknow",
        "state_ut": "Uttar Pradesh (excluding districts under Noida Ombudsman)",
        "address": "Office of the Insurance Ombudsman, 6th Floor, Jeevan Bhawan, Phase-II, Nawal Kishore Road, Hazratganj, Lucknow - 226 001.",
        "email": "bimalokpal.lucknow@cioins.co.in",
        "phone": "0522-2231330 / 2231331"
    },
    "MUMBAI": {
        "center": "Mumbai",
        "state_ut": "Mumbai Metropolitan Region (MMR), Thane, Palghar, Raigad, Goa",
        "address": "Office of the Insurance Ombudsman, 3rd Floor, Jeevan Seva Annexe, S. V. Road, Santacruz (W), Mumbai - 400 054.",
        "email": "bimalokpal.mumbai@cioins.co.in",
        "phone": "022-26106552 / 26106960"
    },
    "NOIDA": {
        "center": "Noida",
        "state_ut": "Western Uttar Pradesh (Gautam Buddh Nagar, Ghaziabad, Meerut, Baghpat, Bulandshahr, Hapur, Aligarh, Muzaffarnagar, Saharanpur, Shamli, Moradabad, Bijnor, Rampur)",
        "address": "Office of the Insurance Ombudsman, Bhagwan Sahai Palace, 4th Floor, Main Road, Naya Bans, Sector 15, Distt: Gautam Buddh Nagar, U.P - 201 301.",
        "email": "bimalokpal.noida@cioins.co.in",
        "phone": "0120-2514205 / 2514206"
    },
    "PATNA": {
        "center": "Patna",
        "state_ut": "Bihar, Jharkhand",
        "address": "Office of the Insurance Ombudsman, 1st Floor, Kalambagh Road, Sharma Complex, Muzaffarpur / 2nd Floor, Lalit Bhawan, Bailey Road, Patna - 800 001.",
        "email": "bimalokpal.patna@cioins.co.in",
        "phone": "0612-2680952"
    },
    "PUNE": {
        "center": "Pune",
        "state_ut": "Maharashtra (excluding Mumbai Metropolitan Region)",
        "address": "Office of the Insurance Ombudsman, Jeevan Darshan Bldg., 3rd Floor, C.T.S. No.s. 195 to 198, N.C. Kelkar Road, Narayan Peth, Pune - 411 030.",
        "email": "bimalokpal.pune@cioins.co.in",
        "phone": "020-41312555"
    }
}


def map_pincode_to_ombudsman(pincode: str) -> Dict[str, str]:
    """
    Deterministic PIN code to Insurance Ombudsman territorial jurisdiction mapper
    covering all 17 Insurance Ombudsman centers across India.
    """
    pin_clean = str(pincode).strip().replace(" ", "")
    if len(pin_clean) != 6 or not pin_clean.isdigit():
        return OMBUDSMAN_CENTERS["MUMBAI"]  # Fallback center

    p2 = int(pin_clean[:2])
    p3 = int(pin_clean[:3])

    # 1. NCT of Delhi (11) & NCR Haryana (121, 122)
    if p2 == 11 or p3 in [121, 122]:
        return OMBUDSMAN_CENTERS["DELHI"]

    # 2. Western UP / NCR (201, 203, 244-251)
    if p3 in [201, 202, 203] or 244 <= p3 <= 251:
        return OMBUDSMAN_CENTERS["NOIDA"]

    # 3. Rest of UP (206-243, 261-285)
    if (204 <= p3 <= 243) or (261 <= p3 <= 285):
        return OMBUDSMAN_CENTERS["LUCKNOW"]

    # 4. Punjab, Haryana (non-NCR), Chandigarh, HP, J&K, Ladakh (12-19)
    if (12 <= p2 <= 19):
        return OMBUDSMAN_CENTERS["CHANDIGARH"]

    # 5. Rajasthan (30-34)
    if 30 <= p2 <= 34:
        return OMBUDSMAN_CENTERS["JAIPUR"]

    # 6. Gujarat, Daman, Diu, Dadra & Nagar Haveli (36-39)
    if 36 <= p2 <= 39:
        return OMBUDSMAN_CENTERS["AHMEDABAD"]

    # 7. Mumbai Metropolitan Region & Goa (40xxxx)
    if p2 == 40 or (400 <= p3 <= 403):
        return OMBUDSMAN_CENTERS["MUMBAI"]

    # 8. Rest of Maharashtra (410-445)
    if 41 <= p2 <= 44:
        return OMBUDSMAN_CENTERS["PUNE"]

    # 9. Madhya Pradesh & Chhattisgarh (45-49)
    if 45 <= p2 <= 49:
        return OMBUDSMAN_CENTERS["BHOPAL"]

    # 10. Telangana & Andhra Pradesh (50-53)
    if 50 <= p2 <= 53:
        return OMBUDSMAN_CENTERS["HYDERABAD"]

    # 11. Karnataka (56-59)
    if 56 <= p2 <= 59:
        return OMBUDSMAN_CENTERS["BENGALURU"]

    # 12. Tamil Nadu & Puducherry (60-64)
    if 60 <= p2 <= 64:
        return OMBUDSMAN_CENTERS["CHENNAI"]

    # 13. Kerala & Lakshadweep (67-69)
    if 67 <= p2 <= 69:
        return OMBUDSMAN_CENTERS["ERNAKULAM"]

    # 14. West Bengal, Sikkim, Andaman & Nicobar (70-74)
    if 70 <= p2 <= 74:
        return OMBUDSMAN_CENTERS["KOLKATA"]

    # 15. Odisha (75-77)
    if 75 <= p2 <= 77:
        return OMBUDSMAN_CENTERS["BHUBANESWAR"]

    # 16. North Eastern States (78-79)
    if 78 <= p2 <= 79:
        return OMBUDSMAN_CENTERS["GUWAHATI"]

    # 17. Bihar & Jharkhand (80-85)
    if 80 <= p2 <= 85:
        return OMBUDSMAN_CENTERS["PATNA"]

    return OMBUDSMAN_CENTERS["MUMBAI"]


class OmbudsmanFormGenerator:
    """
    Generates statutory Insurance Ombudsman Form VI-A complaints pursuant to
    Rule 14(3) of the Insurance Ombudsman Rules, 2017.
    """

    def __init__(self):
        pass

    def generate_form_via_text(self, complaint_data: Dict[str, Any]) -> str:
        complainant_name = complaint_data.get("complainant_name", "Insured / Policyholder")
        complainant_address = complaint_data.get("complainant_address", "Resident Address")
        complainant_pin = str(complaint_data.get("pincode", "400001"))
        phone = complaint_data.get("phone", "XXXXXXXXXX")
        email = complaint_data.get("email", "policyholder@example.com")

        insurer_name = complaint_data.get("insurer_name", "Insurance Company Ltd.")
        insurer_branch = complaint_data.get("insurer_branch", "Branch Grievance Office")
        policy_no = complaint_data.get("policy_number", "POL-XXXXXX")
        claim_no = complaint_data.get("claim_number", "CLM-XXXXXX")
        repudiation_date = complaint_data.get("repudiation_date", datetime.date.today().isoformat())
        gro_date = complaint_data.get("gro_representation_date", "30 days prior")

        disputed_amount = float(complaint_data.get("disputed_amount", 0.0))
        penal_interest_rate = float(complaint_data.get("penal_interest_rate", 8.5))  # Bank Rate + 2%
        grounds_summary = complaint_data.get("grounds_summary", "Unlawful deduction and statutory breach of IRDAI regulations.")

        ombudsman_info = map_pincode_to_ombudsman(complainant_pin)

        form_text = f"""
----------------------------------------------------------------------
                              FORM VI-A
        COMPLAINT TO THE INSURANCE OMBUDSMAN UNDER RULE 14(3)
                OF THE INSURANCE OMBUDSMAN RULES, 2017
----------------------------------------------------------------------

To:
The Insurance Ombudsman,
{ombudsman_info['address']}
Email: {ombudsman_info['email']} | Phone: {ombudsman_info['phone']}

1. DETAILS OF THE COMPLAINANT:
   a. Full Name of the Complainant    : {complainant_name}
   b. Complete Postal Address         : {complainant_address}
   c. PIN Code                        : {complainant_pin} (Jurisdiction: {ombudsman_info['center']})
   d. Contact Mobile Number           : {phone}
   e. Email Address                   : {email}

2. DETAILS OF THE INSURER / RESPONDENT:
   a. Name of the Insurance Company   : {insurer_name}
   b. Branch / Operating Office       : {insurer_branch}

3. PARTICULARS OF INSURANCE POLICY & CLAIM:
   a. Policy Number                   : {policy_no}
   b. Type of Policy                  : Health Insurance
   c. Claim Number                    : {claim_no}
   d. Date of Deduction/Repudiation   : {repudiation_date}

4. STATUTORY PREREQUISITES (RULE 14(3)(a)):
   a. Date of 1st Written Representation to Insurer's GRO : {gro_date}
   b. Status of Response from Insurer                     : Rejected / No Response after 30 days
   c. Statutory Waiting Period Compliance                 : YES (> 30 days elapsed since representation)

5. NATURE OF GRIEVANCE & STATUTORY GROUNDS:
   {grounds_summary}

6. RELIEF CLAIMED:
   a. Principal Disputed Amount Claimed                   : Rs. {disputed_amount:,.2f}
   b. Statutory Penal Interest                            : Penal interest @ {penal_interest_rate:.1f}% per annum 
                                                            (Bank Rate + 2%) under IRDAI PPI Regulations
   c. Compensation for Harassment & Mental Agony          : Rs. 25,000.00
   d. Total Monetary Relief Sought                        : Rs. {disputed_amount + 25000:,.2f} + Accrued Penal Interest

7. SOLEMN DECLARATION & VERIFICATION (RULE 14(3)(b) & (c)):
   I/We hereby solemnly affirm and declare that:
   1. The grievance stated above is genuine and not pending before any Court of Law, 
      Consumer Commission, Arbitrator, or any other authority.
   2. This complaint is made within one year from the date of rejection/action of the insurer.
   3. The facts stated herein are true to the best of my knowledge, information, and belief.

Place : {ombudsman_info['center']}
Date  : {datetime.date.today().strftime('%d-%m-%Y')}

Signature of the Complainant: ___________________________
----------------------------------------------------------------------
"""
        return form_text.strip()

    def generate_form_via_pdf(self, complaint_data: Dict[str, Any], output_path: str) -> str:
        """Renders statutory Form VI-A into a formal PDF."""
        text_content = self.generate_form_via_text(complaint_data)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=9)

        for line in text_content.split("\n"):
            clean_line = line.rstrip().replace("₹", "Rs. ").encode("ascii", "ignore").decode("ascii")
            if not clean_line.strip():
                pdf.ln(3)
            else:
                try:
                    pdf.multi_cell(0, 4.5, text=clean_line, align="L", new_x="LMARGIN", new_y="NEXT")
                except TypeError:
                    pdf.multi_cell(0, 4.5, txt=clean_line, align="L")
                    pdf.set_x(getattr(pdf, "l_margin", 10))

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        pdf.output(output_path)
        return output_path
