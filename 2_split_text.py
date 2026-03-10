import os
import re

def separate_report_sections(input_txt_path, header_out_path, body_out_path):
    print("🚀 Running Strict 4-Step Slicer with Date Stitching...")
    
    if not os.path.exists(input_txt_path):
        print(f"❌ Error: {input_txt_path} not found.")
        return
        
    with open(input_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    # ==========================================
    # 1) SPLIT THE PAGE (Into a list of pages)
    # ==========================================
    page_split_pattern = re.compile(r"(={20,}\s*PAGE\s*\d+\s*={20,})", re.IGNORECASE)
    parts = page_split_pattern.split(full_text)
    
    raw_pages = []
    if len(parts) == 1:
        raw_pages = [full_text]
    else:
        for i in range(1, len(parts), 2):
            raw_pages.append(parts[i] + parts[i+1])

    start_keywords = [
        "HEMATOLOGY", "HAEMATOLOGY", "BIOCHEMISTRY", "CHEMICAL PATHOLOGY", 
        "CLINICAL PATHOLOGY", "TEST NAME", "RESULT", "UNIT", "BIO REF", 
        "INTERVAL", "TEST VALUE"
    ]
    
    end_keywords = [
        "END OF REPORT", "CONSULTANT", "DOCTOR", 
        "NOT VALID FOR MEDICO LEGAL", "PATHOLOGIST"
    ]

    # ==========================================
    # 2) FIND PAGES WHICH HAVE BOTH START AND END WORDS
    # 3) KEEP THOSE PAGES ONLY AND DISCARD OTHER PAGES
    # ==========================================
    kept_pages = []
    
    for page in raw_pages:
        page_upper = page.upper()
        
        # Check if BOTH conditions are true for this specific page
        has_start = any(kw in page_upper for kw in start_keywords)
        has_end = any(kw in page_upper for kw in end_keywords)
        
        if has_start and has_end:
            kept_pages.append(page)
            
    print(f"✅ Steps 1-3 Complete: Kept {len(kept_pages)} valid pages out of {len(raw_pages)} total pages.")

    # ==========================================
    # 4) PERFORM PAGE SEPARATION (Split into Header and Body)
    # ==========================================
    final_header_text = ""
    clean_body_chunks = []

    # Words that usually indicate a date in your reports
    date_catchers = ["DATE", "REPORTED ON", "REPORTED", "DT & TIME", "DT:", "DT :"]

    for page_text in kept_pages:
        lines = page_text.split('\n')
        
        start_idx = 0
        end_idx = len(lines)
        
        # Find where to cut the top
        for i, line in enumerate(lines):
            if any(kw in line.upper() for kw in start_keywords):
                start_idx = i
                break
                
        # Find where to cut the bottom
        for i, line in enumerate(lines):
            if any(kw in line.upper() for kw in end_keywords):
                end_idx = i
                break

        # Slicing the text
        header_lines = lines[:start_idx]
        header = '\n'.join(header_lines).strip()
        body_content = '\n'.join(lines[start_idx:end_idx]).strip()

        # --- START OF NEW DATE STITCHING LOGIC ---
        extracted_dates = []
        for line in header_lines:
            # If the line contains any of the date keywords, grab it
            if any(catcher in line.upper() for catcher in date_catchers):
                extracted_dates.append(line.strip())
        
        # If we found dates, paste them at the top of the body content
        if extracted_dates:
            date_block = '\n'.join(extracted_dates)
            body = f"--- DATES ---\n{date_block}\n{body_content}"
        else:
            body = body_content
        # --- END OF NEW DATE STITCHING LOGIC ---

        # Append to our final strings
        final_header_text += header + "\n\n"
        clean_body_chunks.append(body)

    final_body_text = '\n\n==========================================\n\n'.join(clean_body_chunks).strip()

    # Save outputs
    with open(header_out_path, 'w', encoding='utf-8') as f:
        f.write(final_header_text.strip())
        
    with open(body_out_path, 'w', encoding='utf-8') as f:
        f.write(final_body_text)
        
    print("✅ Step 4 Complete: Files successfully separated and saved.")

if __name__ == "__main__":
    separate_report_sections(
        'final_tesseract_output.txt', 
        'header_data.txt', 
        'medical_body_data.txt'
    )