import sqlite3
import json
import os
from db_schema import DB_NAME
from section_mapping import TEST_TO_SECTION_MAP

def get_connection():
    return sqlite3.connect(DB_NAME)

# --- 1. INSERTION OPERATIONS (Pipeline Bridge) ---

def add_patient(name, age, gender):
    """Inserts a patient and returns their unique ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # We use INSERT OR IGNORE to avoid duplicates if the schema enforces unique constraints
        cursor.execute("INSERT OR IGNORE INTO patients (name, age, gender) VALUES (?, ?, ?)", 
                       (name, age, gender))
        conn.commit()
        # Retrieve the ID of the patient we just inserted/found
        cursor.execute("SELECT patient_id FROM patients WHERE name=? AND age=?", (name, age))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def import_json_to_db(json_path):
    """Parses JSON and migrates it into the database using Section Mapping."""
    if not os.path.exists(json_path):
        return False

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    p = data.get("patient_details", {})
    # Safety check for missing patient details
    if not p: return False
    
    pid = add_patient(p.get('name', 'Unknown'), p.get('age', 0), p.get('gender', 'Unknown'))

    conn = get_connection()
    cursor = conn.cursor()

    results = data.get("results", {})
    for date, tests in results.items():
        for test_name, details in tests.items():
            # Handling Regular Tests
            if isinstance(details, dict) and "value" in details:
                category = TEST_TO_SECTION_MAP.get(test_name, "GENERAL")
                cursor.execute('''
                    INSERT INTO test_results (patient_id, report_date, category, test_name, value, unit, ref_range, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pid, date, category, test_name, str(details['value']), details.get('unit', ''), details.get('reference_range', ''), details.get('status', '')))
            
            # Handling Urine Routine (Nested)
            elif test_name == "URINE_ROUTINE":
                for section, utests in details.items():
                    for utest_name, udetails in utests.items():
                        cursor.execute('''
                            INSERT INTO test_results (patient_id, report_date, category, test_name, value, unit, ref_range, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (pid, date, "URINE ROUTINE", utest_name, str(udetails.get('value')), udetails.get('unit', ''), udetails.get('reference', ''), "N/A"))

    conn.commit()
    conn.close()
    return True

# --- 2. RETRIEVAL OPERATIONS (Streamlit Display) ---

def get_all_patients():
    """Returns a list of all patients."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT patient_id, name, age, gender FROM patients")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_patient_report(pid):
    """Returns all tests for a specific patient."""
    conn = get_connection()
    cursor = conn.cursor()
    # CRITICAL FIX: We select columns explicitly so app.py receives them in the right order
    # Order: ResultID, Date, Category, Name, Value, Unit, Range, Status
    cursor.execute("""
        SELECT result_id, report_date, category, test_name, value, unit, ref_range, status 
        FROM test_results 
        WHERE patient_id=? 
        ORDER BY report_date DESC
    """, (pid,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- 3. EDIT/DELETE OPERATIONS (Streamlit Interaction) ---

def update_patient_metadata(pid, name, age, gender):
    """Updates Name, Age, or Gender."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE patients 
        SET name=?, age=?, gender=? 
        WHERE patient_id=?
    ''', (name, age, gender, pid))
    conn.commit()
    conn.close()

# --- NEW FUNCTIONS FOR YOUR APP UPGRADE ---

# def delete_patient_completely(pid):
#     """Deletes the patient AND all their test records."""
#     conn = get_connection()
#     cursor = conn.cursor()
#     try:
#         # 1. Delete all test results for this patient
#         cursor.execute("DELETE FROM test_results WHERE patient_id=?", (pid,))
#         # 2. Delete the patient metadata
#         cursor.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
#         conn.commit()
#     except Exception as e:
#         print(f"Error deleting patient: {e}")
#     finally:
#         conn.close()


import os

def delete_patient_completely(patient_id):
    """Deletes a patient from the DB and removes all their saved PDF reports."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Delete from Database
    cursor.execute("DELETE FROM test_results WHERE patient_id = ?", (patient_id,))
    cursor.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
    conn.commit()
    conn.close()
    
    # 2. Delete the actual PDF files from the folder
    folder = "uploaded_reports"
    if os.path.exists(folder):
        for file in os.listdir(folder):
            # Find any file that starts with this patient's ID (e.g., "62_")
            if file.startswith(f"{patient_id}_") and file.endswith(".pdf"):
                try:
                    os.remove(os.path.join(folder, file))
                    print(f"✅ Deleted orphaned file: {file}")
                except Exception as e:
                    print(f"⚠️ Could not delete file {file}: {e}")

def update_test_record(result_id, val, unit, ref_range, status):
    """Updates all details of a specific test record."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE test_results 
            SET value=?, unit=?, ref_range=?, status=? 
            WHERE result_id=?
        ''', (val, unit, ref_range, status, result_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating record: {e}")
    finally:
        conn.close()


# --- NEW: MANUAL ADD & DELETE SPECIFIC TESTS ---

def add_manual_test_record(patient_id, report_date, category, test_name, value, unit, ref_range, status):
    # Connect to your database
    conn = sqlite3.connect("reportlens_lab.db")
    cursor = conn.cursor()

    # ==========================================================
    # 👇 ADD THIS BLOCK: Force all inputs to be plain strings 👇
    # ==========================================================
    def sanitize(var):
        if isinstance(var, dict):
            # If AI returns a dict, grab the first value inside it
            return str(next(iter(var.values()))) if var else ""
        elif isinstance(var, list):
            # If AI returns a list, join it with commas
            return ", ".join(map(str, var))
        elif var is None:
            return ""
        return str(var)

    category = sanitize(category)
    test_name = sanitize(test_name)
    value = sanitize(value)
    unit = sanitize(unit)
    ref_range = sanitize(ref_range)
    status = sanitize(status)
    # ==========================================================

    # Now execute the query safely
    cursor.execute('''
        INSERT INTO test_results (patient_id, report_date, category, test_name, value, unit, ref_range, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (patient_id, report_date, category, test_name, value, unit, ref_range, status))
    
    conn.commit()
    conn.close()

def delete_test_record(result_id):
    """Deletes a specific test row by its unique ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_results WHERE result_id=?", (result_id,))
    conn.commit()
    conn.close()


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