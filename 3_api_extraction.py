import os
import json
from dotenv import load_dotenv
from groq import Groq

# 🔥 1. IMPORT YOUR OFFICIAL DICTIONARY
from section_mapping import TEST_TO_SECTION_MAP

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_ai_response(system_message, user_content):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.0 # Strict accuracy
    )
    return json.loads(completion.choices[0].message.content)

def main():
    # Load your files
    def read_file(name):
        try:
            with open(name, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except: return ""

    header_text = read_file("header_data.txt")
    test_text = read_file("medical_body_data.txt")
    ckd_ref = read_file("ckd_reference.json")

    # 🔥 2. GET THE LIST OF PERFECT TEST NAMES
    official_test_names = list(TEST_TO_SECTION_MAP.keys())

    # --- STEP 1: STRICT HEADER EXTRACTION ---
    header_system = """
    Extract patient details with these strict cleaning rules:
    
    1. NAME: Remove ALL prefixes/initials (Mr, Ms, Mrs, Master, Dr, Shri, Smt). 
       Example: "Mr. Venkappa Bangera" -> "Venkappa Bangera"
    2. AGE: Return ONLY the digits. Remove 'Y', 'Years', 'Yr', 'Old'.
       Example: "78 Years" -> "78"
    3. GENDER: Standardize to exactly "Male" or "Female".
       Example: "M" -> "Male", "F" -> "Female", "MALE" -> "Male".

    Output JSON format: {"name": "...", "age": "...", "gender": "..."}
    """
    print("📋 Extracting and Cleaning Patient Header...")
    patient_details = get_ai_response(header_system, header_text)

    # --- STEP 2: TEST DETAILS WITH DATE GROUPING ---
    medical_system = f"""
    You are a medical data auditor. Extract tests using this reference list: {ckd_ref}
    
    STRICT RULES:
    1. DATE: Find the report date for every test. Group results under the date in 'DD-MM-YY' format.
    
    2. AUTOCORRECT TEST NAMES: Compare the test names in the document against this official list: 
       {official_test_names}
       If a test closely matches one on this list (even with typos or missing letters), you MUST output the exact official name from the list. If it is completely unknown, output it as written.
       
    3. VALUES: Do NOT predict or change values. Take exactly what is in the text.

    4.3. SPECIAL PH LOGIC: 
       - If the test is 'pH' AND there is a reference range provided in the text (e.g., 7.35-7.45), name it exactly "PH (BLOOD)".
       - If the test is 'pH' AND there is NO reference range provided in the text, name it exactly "PH".

    5. STATUS: Compare the 'value' to the 'reference_range'. 
       - If higher: "High"
       - If lower: "Low"
       - If within: "Normal"
    6. FORMAT: Use the specific nested JSON structure requested.

    Requested JSON Structure:
    {{
      "results": {{
        "DD-MM-YY": {{
          "TEST NAME": {{ "value": 0, "unit": "..", "reference_range": "..", "status": ".." }}
        }}
      }}
    }}
    """
    print("🔬 Processing Medical Tests (Grouping by Date)...")
    medical_results = get_ai_response(medical_system, test_text)

    # --- STEP 3: COMBINE INTO ONE FILE ---
    final_output = {
        "patient_details": patient_details,
        "results": medical_results.get("results", {})
    }

    # Save final JSON
    output_filename = "final_clean_output.json"
    with open(output_filename, "w") as f:
        json.dump(final_output, f, indent=2)

    print(f"\n✅ All Done! Combined file saved as: {output_filename}")
    print(json.dumps(final_output, indent=2))

if __name__ == "__main__":
    main()