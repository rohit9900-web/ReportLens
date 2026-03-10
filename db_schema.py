import sqlite3

DB_NAME = "reportlens_lab.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table 1: Patients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT 
        )
    ''')
    
    # Table 2: Test Results with Category Column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            report_date TEXT,
            category TEXT,       -- Group (e.g., COMPLETE BLOOD COUNT)
            test_name TEXT,      -- Individual test name
            value TEXT,
            unit TEXT,
            ref_range TEXT,
            status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Schema initialized with Category support.")

if __name__ == "__main__":
    create_tables()