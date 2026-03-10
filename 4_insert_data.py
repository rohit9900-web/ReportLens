import json
import os
import db_manager
from section_mapping import TEST_TO_SECTION_MAP

JSON_INPUT = "final_clean_output.json"

def run_insertion():
    if not os.path.exists(JSON_INPUT):
        print(f" Error: {JSON_INPUT} not found.")
        return

    with open(JSON_INPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    p = data.get("patient_details", {})
    pid = db_manager.add_patient(p['name'], p['age'], p['gender'])
    print(f" Processing Report for: {p['name']} (ID: {pid})")

    for date, tests in data.get("results", {}).items():
        for test_name, details in tests.items():
            if isinstance(details, dict) and "value" in details:
                category = TEST_TO_SECTION_MAP.get(test_name, "GENERAL")
                
                # POSITIONAL ARGUMENTS ONLY (No 'range=' to prevent the crash)
                db_manager.add_manual_test_record(
                    pid,
                    date,
                    category,
                    test_name,
                    str(details.get('value', 'N/A')),
                    details.get('unit', 'N/A'),
                    details.get('reference_range', 'N/A'),
                    details.get('status', 'Unknown')
                )
            
            elif test_name == "URINE_ROUTINE":
                for section_name, urine_tests in details.items():
                    for u_name, u_details in urine_tests.items():
                        db_manager.add_manual_test_record(
                            pid,
                            date,
                            "URINE ROUTINE",
                            u_name,
                            str(u_details.get('value', 'N/A')),
                            u_details.get('unit', 'N/A'),
                            u_details.get('reference', 'N/A'),
                            u_details.get('status', 'N/A')
                        )

    print(" All data has been successfully moved to the database!")



# --- POSITION: db_manager.py ---
def factory_reset_db():
    import sqlite3
    import os
    import shutil
    
    conn = sqlite3.connect("reportlens_lab.db")
    cursor = conn.cursor()
    
    # 1. Clear SQL Tables
    cursor.execute("DELETE FROM test_results")
    cursor.execute("DELETE FROM patients")
    cursor.execute("DELETE FROM sqlite_sequence") # Resets IDs to 1
    
    # 2. 🔥 DELETE ALL UPLOADED PDF FILES
    # This specifically removes the folder where "Abdul Salam V.pdf" etc. are stored
    if os.path.exists("uploaded_reports"):
        shutil.rmtree("uploaded_reports") 
        os.makedirs("uploaded_reports") # Recreate the empty folder for new uploads
        
    conn.commit()
    conn.close()
    print("Database and PDF storage have been wiped clean.")

if __name__ == "__main__":
    run_insertion()