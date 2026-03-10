import re
import json
import os

def process_and_extract(input_path, output_json):
    if not os.path.exists(input_path):
        print(f" Error: {input_path} not found.")
        return False

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    # --- 1. PAGE SPLITTING ---
    page_split_pattern = re.compile(r"(={20,}\s*PAGE\s*\d+\s*={20,})", re.IGNORECASE)
    parts = page_split_pattern.split(full_text)
    
    raw_pages = []
    for i in range(1, len(parts), 2):
        raw_pages.append(parts[i] + parts[i+1])

    personal_info = {"name": "Not Found", "age": "Not Found", "gender": "Not Found"}
    all_test_blocks = []
    
    SECTION_MARKERS = [
        "HEMATOLOGY", "HAEMATOLOGY", "BIOCHEMISTRY", "CHEMICAL PATHOLOGY", 
        "CLINICAL PATHOLOGY", "TEST NAME", "RESULT", "UNIT", "BIO REF", 
        "INTERVAL", "TEST VALUE"
    ]

    print(f" [Processing] Analyzing {len(raw_pages)} pages...")

    for i, page_text in enumerate(raw_pages):
        page_num = i + 1
        lines = page_text.split('\n')
        
        # ==========================================
        # 1. WATERFALL NAME DETECTION (Fires Once)
        # ==========================================
        if personal_info["name"] == "Not Found":
            raw_name = ""
            # Search only the top portion of the page for headers
            search_area = lines[:35]
            
            # --- PRIORITY 1: Search for "Name :" or "Patient :" labels ---
            for idx, line in enumerate(search_area):
                clean_line = line.strip()
                
                # ADDED \b HERE: This prevents it from matching "name" inside "yourlabname"
                name_m = re.search(r"(?i)\b(?:NAME|PATIENT|NM)\b\s*[:\- \.=>]+\s*(.*)", clean_line)
                
                if name_m:
                    candidate = name_m.group(1).strip()
                    if len(candidate) > 1:
                        raw_name = candidate
                        break  # Stop looking! We found it.
                    elif len(candidate) <= 1 and idx + 1 < len(search_area):
                        # Next-line fallback if the label was empty
                        next_line = search_area[idx+1].strip()
                        # Ensure the next line isn't an email or numbers before grabbing it
                        if not re.search(r'(?i)(@|www\.|\.com|\.in|\.org|gmail|email)', next_line) and not re.search(r'\d{3,}', next_line):
                            raw_name = next_line
                            break
            
            # --- PRIORITY 2: If Priority 1 failed, search for Titles ---
            if not raw_name:
                for line in search_area:
                    clean_line = line.strip()
                    title_m = re.search(r"(?i)\b(MR|MRS|MS|MISS|MASTER|BABY|DR)\.?\s*([A-Za-z]+\s*[A-Za-z]*)", clean_line)
                    if title_m:
                        raw_name = title_m.group(0).strip()
                        break  # Stop looking! We found a title.

            # --- PRIORITY 3: If 1 & 2 failed, find the line near "Age/Sex" ---
            if not raw_name:
                for idx, line in enumerate(search_area):
                    clean_line = line.strip()
                    if idx > 0 and re.search(r"(?i)\b(?:AGE|YRS|YEARS|SEX|GENDER)\b", clean_line):
                        prev_line = search_area[idx-1].strip()
                        # Check to make sure the previous line isn't junk data
                        if len(prev_line) > 2 and not re.search(r'(?i)(@|www\.|\.com|\.in|\.org|gmail|email)', prev_line) and not re.search(r'\d{3,}', prev_line):
                            raw_name = prev_line
                            break

            # --- 4. AFTER OTHER LOGICS (Cleaning & Formatting) ---
            if raw_name:
                val = raw_name
                
                # A. Chop off adjacent medical artifacts 
                # ADDED: REG, LAB, NO, REF, UHID, PID to instantly cut off registration numbers
                val = re.split(r'(?i)\b(?:AGE|GENDER|SEX|ID|DATE|D\.O\.D|REG|LAB|NO|REF|UHID|PID)\b', val)[0].strip()
                
                # B. Remove the Titles so we just have the pure name
                val = re.sub(r'(?i)\b(MR|MRS|MS|MISS|MASTER|BABY|DR)\.?\s*', '', val).strip()
                
                # C. Strip leading/trailing garbage punctuation AND numbers (fixes ":" and "25083913")
                # The \d removes any stray numbers at the end of the name
                val = re.sub(r'^[\W_\d]+|[\W_\d]+$', '', val).strip()
                
                # D. Final Safety Check (Absolutely no emails or domains allowed)
                if len(val) > 2 and not re.search(r'(?i)(@|www\.|\.com|\.in|\.org|gmail|email)', val):
                    personal_info["name"] = val.title()

        # ==========================================
        # 2. METADATA & TEST EXTRACTION
        # ==========================================
        for idx, line in enumerate(lines):
            clean_line = line.strip()

            # --- AGE & GENDER DETECTION ---
            comb_p = r"(?i)(?:AGE|YRS|YEARS)\s*[:\-/]?\s*(?:SEX|GENDER)?\s*[:\-/]?\s*(\d+)\s*(?:YRS|YR)?\s*/\s*(MALE|FEMALE|M|F)"
            comb_m = re.search(comb_p, clean_line)
            if comb_m:
                personal_info["age"] = comb_m.group(1)
                personal_info["gender"] = comb_m.group(2)
            else:
                if personal_info["age"] == "Not Found":
                    age_m = re.search(r"(?i)\bAGE\b\s*[:\-/\s]*(\d+)", clean_line)
                    if age_m and "PAGE" not in clean_line.upper():
                        personal_info["age"] = age_m.group(1)
                if personal_info["gender"] == "Not Found":
                    gen_m = re.search(r"(?i)\b(?:SEX|GENDER)\b\s*[:\-/\s]*(MALE|FEMALE|M|F)", clean_line)
                    if gen_m:
                        personal_info["gender"] = gen_m.group(1)

        # --- B. TEST LINE EXTRACTION (SKIPS PAGE 1) ---
        # if page_num == 1:
        #     continue # <--- This prevents Page 1 test lines from saving to JSON

        page_test_lines = []
        in_zone = False
        report_date = "Not Found"

        for line in lines:
            if re.search(r'(?i)DATE\s*:', line):
                date_m = re.search(r"(\d{2}[/-]\d{2}[/-]\d{2,4})", line)
                if date_m: report_date = date_m.group(1)

            if any(marker in line.upper() for marker in SECTION_MARKERS):
                in_zone = True
                continue 
            
            if any(e in line.upper() for e in ["END OF REPORT", "CONSULTANT", "DOCTOR"]):
                in_zone = False
                break 
            
            if in_zone:
                page_test_lines.append(line.strip())

        if page_test_lines:
            all_test_blocks.append({
                "date": report_date, 
                "lines": page_test_lines
            })

    # --- 3. FINAL NORMALIZATION ---
    if personal_info["gender"] != "Not Found":
        g = personal_info["gender"].upper()
        personal_info["gender"] = "Male" if g.startswith("M") else "Female"

    final_output = {
        "patient_details": personal_info,
        "lab_results": all_test_blocks
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)

    print("-" * 30)
    print(f" EXTRACTION SUCCESS")
    print(f" Name   : {personal_info['name']}")
    print(f" Age    : {personal_info['age']}")
    print(f" Gender : {personal_info['gender']}")
    return True

if __name__ == "__main__":
    process_and_extract('final_tesseract_output.txt', 'extracted_lab_data.json')