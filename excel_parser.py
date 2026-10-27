import os
import re
import pandas as pd
from typing import List, Dict, Any, Tuple

def clean_phone_number(phone_raw: Any, default_country_code: str = "91") -> str:
    """Normalize phone number to international format with country code."""
    if pd.isna(phone_raw):
        return ""
    
    # Convert to string and strip decimals if read as float
    phone_str = str(phone_raw).split('.')[0].strip()
    # Remove all non-numeric characters except leading '+'
    digits = re.sub(r"[^\d+]", "", phone_str)
    
    if not digits:
        return ""
        
    # If starts with '+', strip '+' for WhatsApp web format
    if digits.startswith("+"):
        return digits[1:]
        
    # If 10 digits (typical India or US without country code)
    if len(digits) == 10:
        return f"{default_country_code.lstrip('+')}{digits}"
        
    # If starts with '0' and 11 digits (e.g., 09876543210 in India)
    if digits.startswith("0") and len(digits) == 11:
        return f"{default_country_code.lstrip('+')}{digits[1:]}"
        
    return digits

def parse_leads_file(file_path: str, default_country_code: str = "91") -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parses Excel (.xlsx, .xls) or CSV file and detects Name, Email, Phone, and Company columns.
    Returns: (records_list, available_columns_list)
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    elif ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload .xlsx, .xls, or .csv")
        
    # Clean column headers
    df.columns = [str(col).strip() for col in df.columns]
    original_columns = list(df.columns)
    
    # Intelligent column mapping (case-insensitive)
    name_col = None
    email_col = None
    phone_col = None
    company_col = None
    
    for col in original_columns:
        c_lower = col.lower()
        if not name_col and any(k in c_lower for k in ["name", "contact person", "full name", "first name", "agent"]):
            name_col = col
        elif not email_col and any(k in c_lower for k in ["email", "e-mail", "mail"]):
            email_col = col
        elif not phone_col and any(k in c_lower for k in ["phone", "mobile", "whatsapp", "cell", "contact number"]):
            phone_col = col
        elif not company_col and any(k in c_lower for k in ["company", "agency", "business", "organization", "firm"]):
            company_col = col

    records = []
    for idx, row in df.iterrows():
        rec = {}
        # Keep all original column data
        for col in original_columns:
            val = row[col]
            rec[col] = "" if pd.isna(val) else str(val).strip()
            
        # Standardized core properties
        rec["_id"] = idx + 1
        rec["_name"] = rec.get(name_col, "") if name_col else ""
        rec["_email"] = rec.get(email_col, "") if email_col else ""
        rec["_company"] = rec.get(company_col, "") if company_col else ""
        
        raw_phone = rec.get(phone_col, "") if phone_col else ""
        rec["_raw_phone"] = raw_phone
        rec["_clean_phone"] = clean_phone_number(raw_phone, default_country_code)
        
        rec["_status_email"] = "Pending"
        rec["_status_whatsapp"] = "Pending"
        records.append(rec)
        
    return records, original_columns
