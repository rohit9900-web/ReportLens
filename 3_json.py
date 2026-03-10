import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from section_mapping import TEST_TO_SECTION_MAP

# Paths
REFERENCE_PATH = Path("D:/ReportLens/ckd_reference.json")
EXTRACTED_PATH = Path("D:/ReportLens/extracted_lab_data.json")
OUTPUT_PATH = Path("D:/ReportLens/final_clean_output.json")

# Config
FUZZY_THRESHOLD = 0.87
HPF_KEYWORDS = ["/HPF", "HPF"]

def normalize(s: Optional[str]) -> str:
    if s is None: return ""
    s = s.upper().strip()
    
    # NEW: Removes leading dots, dashes, or symbols (fixes ". SODIUM")
    s = re.sub(r"^[^A-Z0-9]+", "", s) 
    
    s = re.sub(r"\s+", " ", s)
    s = s.replace("QM/DL", "GM/DL").replace("MA/L", "MG/L")
    s = s.replace("LILIRUBIN", "BILIRUBIN").replace("QTHERS", "OTHERS")
    s = s.replace("MICROSCOPI", "MICROSCOPIC")
    return s

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def first_number(text: str):
    m = re.search(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", text)
    if not m: return None
    return float(m.group(0).replace(",", ""))

def find_range(text: str) -> Optional[str]:
    m = re.search(r"(-?\d+(\.\d+)?)\s*[-–]\s*(-?\d+(\.\d+)?)", text)
    if m: return f"{m.group(1)} - {m.group(3)}"
    return None

def extract_unit(text: str) -> Optional[str]:
    units = re.search(r"(MG/DL|GM/DL|G/DL|MEQ/L|MILLI?EQUIV/L|MILL|%|FL|LAKH/CUMM|CELLS/CUMM|MILL/CUMM|NG/ML|U/L|PG|/HPF|MG/L|ML)", text, re.IGNORECASE)
    return units.group(1) if units else None

def pick_best_match_smart(name_candidate: str, line_text: str, refs: list, gender: str) -> Tuple[Optional[dict], float]:
    best_ref, score = pick_best_ref_match(name_candidate, refs)
    if score >= 0.90: 
        return best_ref, score

    extracted_range = find_range(line_text)
    if extracted_range:
        possible_matches = []
        for r in refs:
            ref_val = r.get("reference")
            if isinstance(ref_val, dict):
                ref_val = ref_val.get(gender, ref_val.get("Male"))
            if str(extracted_range) == str(ref_val):
                possible_matches.append(r)

        if len(possible_matches) == 1:
            return possible_matches[0], 0.90 
        if len(possible_matches) > 1:
            best_partial = None
            best_partial_score = 0
            for p in possible_matches:
                p_score = similarity(normalize(name_candidate), p["name"])
                if p_score > best_partial_score:
                    best_partial_score = p_score
                    best_partial = p
            return best_partial, 0.91

    return best_ref, score


def pick_best_match_smart(name_candidate: str, line_text: str, refs: list, gender: str) -> Tuple[Optional[dict], float]:
    best_ref, score = pick_best_ref_match(name_candidate, refs)
    if score >= FUZZY_THRESHOLD:
        return best_ref, score

    extracted_range = find_range(line_text)
    if extracted_range:
        clean_ext = re.sub(r',(\d{3})(?!\d)', r'\1', extracted_range)
        clean_ext = clean_ext.replace(",", ".").replace(" ", "")
        
        for r in refs:
            ref_raw = r.get("reference")
            
            # ALLOW MULTIPLE RANGES (Dict or List)
            possible_refs = []
            if isinstance(ref_raw, dict):
                possible_refs.extend(ref_raw.values())
            elif isinstance(ref_raw, list):
                possible_refs.extend(ref_raw)
            else:
                possible_refs.append(ref_raw)
            
            for rv in possible_refs:
                if not rv: continue
                clean_ref = re.sub(r',(\d{3})(?!\d)', r'\1', str(rv))
                clean_ref = clean_ref.replace(",", ".").replace(" ", "")
                
                if clean_ext == clean_ref:
                    return r, 0.99 
                    
                try:
                    ext_parts = re.findall(r"[-+]?\d*\.\d+|\d+", clean_ext)
                    ref_parts = re.findall(r"[-+]?\d*\.\d+|\d+", clean_ref)
                    if len(ext_parts) == 2 and len(ref_parts) == 2:
                        if float(ext_parts[0]) == float(ref_parts[0]) and float(ext_parts[1]) == float(ref_parts[1]):
                            return r, 0.99
                except Exception:
                    pass

    return best_ref, score

def pick_best_ref_match(name_candidate: str, refs: list, threshold: float = FUZZY_THRESHOLD) -> Tuple[Optional[dict], float]:
    candidate = normalize(name_candidate)
    best = None; best_score = 0.0
    for r in refs:
        score = similarity(candidate, r["name"])
        if score > best_score:
            best_score = score
            best = r
    if best_score >= threshold:
        return best, best_score
    return None, best_score


def status_from_value_and_ref(value_str: Optional[str], ref_range: Optional[Any]) -> str:
    if value_str is None or ref_range is None: return "Unknown"
    if re.search(r"\d+\s*[-–]\s*\d+.*HPF", value_str, re.IGNORECASE): return "Unknown"
    
    # SMART COMMA FIX FOR THE EXTRACTED VALUE (e.g., 7,730.0 -> 7730.0)
    val_clean = re.sub(r',(\d{3})(?!\d)', r'\1', str(value_str))
    val_clean = val_clean.replace(",", ".")
    
    m_val = re.search(r"-?\d+(\.\d+)?", val_clean)
    if not m_val: return "Unknown"
    
    try:
        val = float(m_val.group(0))
    except Exception:
        return "Unknown"
        
    if isinstance(ref_range, dict): return "Unknown"
    
    # SMART COMMA FIX FOR REFERENCE RANGE (e.g., 4,000 -> 4000 and 136,00 -> 136.00)
    rr = re.sub(r',(\d{3})(?!\d)', r'\1', str(ref_range))
    rr = rr.replace(",", ".")
    
    m = re.search(r"(-?\d+(\.\d+)?)\s*[-–]\s*(-?\d+(\.\d+)?)", rr)
    
    if m:
        low = float(m.group(1))
        high = float(m.group(3))
        if val < low: return "Low"
        if val > high: return "High"
        return "Normal"
        
    m_lt = re.search(r"<\s*([0-9.]+)", rr)
    m_gt = re.search(r">\s*([0-9.]+)", rr)
    if m_lt: return "Normal" if val <= float(m_lt.group(1)) else "High"
    if m_gt: return "High" if val >= float(m_gt.group(1)) else "Normal"
    
    return "Unknown"

def load_reference(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    flat = []
    for category, tests in raw.items():
        for tname, meta in tests.items():
            flat.append({
                "name": normalize(tname),
                "original_name": tname,
                "category": normalize(category),
                "expected_unit": meta.get("expected_units"),
                "reference": meta.get("reference_ranges") or meta.get("reference_range")
            })
    return flat


def parse_urine_lines(lines: list, refs: list, gender: Optional[str]):
    out = {"PHYSICAL_EXAMINATION": {}, "CHEMICAL_EXAMINATION": {}, "MICROSCOPIC_EXAMINATION": {}, "_LIVER_SPILLOVER": {}}
    current_section = None
    physical_keys = ["VOLUME", "PH", "COLOUR", "APPEARANCE", "SPECIFIC GRAVITY"]
    chemical_keys = ["ALBUMIN", "SUGAR"]
    micro_keys = ["RBCS", "PUS CELLS", "EPITHELIAL", "CASTS", "CRYSTALS", "OTHERS"]
    
    all_keys = sorted(physical_keys + chemical_keys + micro_keys, key=len, reverse=True)

    for raw in lines:
        ln = normalize(raw)
        if not ln: continue
        if "PHYSICAL" in ln: current_section = "PHYSICAL_EXAMINATION"; continue
        if "CHEMICAL" in ln: current_section = "CHEMICAL_EXAMINATION"; continue
        if "MICRO" in ln: current_section = "MICROSCOPIC_EXAMINATION"; continue
        
        ln_clean = re.sub(r"^[\d\W_]+", "", ln).strip()
        ln_clean = re.sub(r"^[\-\|]+", "", ln_clean).strip()

        if current_section is None:
            if any(k in ln_clean for k in physical_keys): current_section = "PHYSICAL_EXAMINATION"
            elif any(k in ln_clean for k in chemical_keys): current_section = "CHEMICAL_EXAMINATION"
            elif any(k in ln_clean for k in micro_keys): current_section = "MICROSCOPIC_EXAMINATION"
        if current_section is None: continue

        found_key = None
        rest = ""
        for k in all_keys:
            if ln_clean.startswith(k):
                found_key = k
                rest = ln_clean[len(k):].strip()
                rest = re.sub(r"^[:\-\s]+", "", rest)
                break
        
        if found_key:
            tname = found_key
        else:
            m = re.match(r"([A-Z0-9 \(\)]+?)\s+(.+)$", ln_clean)
            if not m: continue
            tname = normalize(m.group(1)).strip()
            rest = m.group(2).strip()
            
        tkey = re.sub(r"[^A-Z ]", "", tname).strip()

        # ========================================================
        # ALBUMIN FIX: If it has a number, kick it to Liver section
        # ========================================================
        if "ALBUMIN" in tkey:
            if re.search(r"\d", rest): # It's a number (e.g. 4.1 gm/dL)
                out["_LIVER_SPILLOVER"]["ALBUMIN"] = rest
                continue # Skip putting it into Urine!
            else:
                tkey = "ALBUMIN" # Safe to keep in Urine

        if current_section == "MICROSCOPIC_EXAMINATION":
            val_hpf = re.search(r"(\d+\s*[-–]\s*\d+\s*/\s*hpf|\d+(\.\d+)?\s*/\s*hpf)", rest, re.IGNORECASE)
            simple_range = find_range(rest)
            kval = None; kref = None
            if val_hpf:
                kval = val_hpf.group(1).replace(" ", "")
                all_ranges = re.findall(r"(\d+\s*[-–]\s*\d+)", rest)
                if len(all_ranges) >= 2: kref = all_ranges[1].replace(" ", "")
            elif simple_range: kval = simple_range
            elif "NIL" in rest: kval = "Nil"
            else: kval = rest

            key = tkey
            if "RBC" in tkey: key = "RBCs"
            elif "PUS" in tkey: key = "PUS CELLS"

            entry = {"value": kval}
            if kref: entry["reference"] = kref
            refmatch, score = pick_best_ref_match(key, refs)
            if refmatch and refmatch.get("reference"):
                rref = refmatch["reference"]
                if isinstance(rref, dict) and gender: rref = rref.get(gender, rref)
                entry.setdefault("reference", rref)
            out["MICROSCOPIC_EXAMINATION"][key] = entry
        else:
            out[current_section][tkey] = {"value": rest}
    return out


def main():
    reference_flat = load_reference(REFERENCE_PATH)
    refs_by_category = {}
    for r in reference_flat:
        refs_by_category.setdefault(r["category"], []).append(r)

    extracted = json.loads(EXTRACTED_PATH.read_text(encoding="utf-8"))
    patient = extracted.get("patient_details", {})
    gender = patient.get("gender", "Male")

    final = {"patient_details": patient, "results": {}}

    for block in extracted.get("lab_results", []):
        date = block.get("date", "unknown")
        lines = block.get("lines", [])
        nlines = [normalize(l) for l in lines if l and l.strip()]
        final["results"].setdefault(date, {})

        urine_indices = [i for i, ln in enumerate(nlines) if "URINE" in ln]
        start, end = 0, 0

        # --- POSITION: Inside main() -> if urine_indices: ---
        if urine_indices:
            # ... (keep your existing start/end logic) ...
            urine_struct = parse_urine_lines(nlines[start:end], refs_by_category.get("URINE ROUTINE", reference_flat), gender)
            
            # 🔥 NEW: Flatten the three urine sub-sections into one flat dictionary
            flat_urine = {}
            for sub_section in ["PHYSICAL_EXAMINATION", "CHEMICAL_EXAMINATION", "MICROSCOPIC_EXAMINATION"]:
                flat_urine.update(urine_struct.get(sub_section, {}))
            
            # Save directly to URINE_ROUTINE key
            final["results"][date]["URINE_ROUTINE"] = flat_urine

            # Handle Albumin Liver Spillover
            liver_spills = urine_struct.pop("_LIVER_SPILLOVER", {})
            if "ALBUMIN" in liver_spills:
                sp_v = liver_spills["ALBUMIN"]
                valnum = first_number(sp_v)
                final["results"][date]["ALBUMIN"] = {
                    "value": valnum,
                    "unit": "gm/dL",
                    "reference_range": "3.5 - 5.2",
                    "status": status_from_value_and_ref(str(valnum), "3.5 - 5.2")
                }

    
        # --- POSITION: General Test Loop (Replaces your existing loop) ---
        for i, raw in enumerate(nlines):
            if urine_indices and start <= i < end: continue
            ln = raw
            if len(ln) < 3: continue

            m_num = re.search(r"-?\d+(\.\d+)?", ln)
            name_candidate = ln[:m_num.start()].strip() if m_num else ln.strip()
            
            non_urine_refs = [r for r in reference_flat if "URINE" not in r["category"]]
            ref_match, score = pick_best_match_smart(name_candidate, ln, non_urine_refs, gender)
            
            if ref_match and score >= FUZZY_THRESHOLD:
                canonical = ref_match["original_name"]
                
                # 🔥 NEW PH LOGIC: If range exists in text, it is Blood Gas
                extracted_range = find_range(ln)
                if canonical.upper() == "PH":
                    if extracted_range:
                        canonical = "PH (BLOOD)" # Maps to ABG in section_mapping.py
                    else:
                        canonical = "PH" # Maps to Urine in section_mapping.py
                
                valnum = first_number(ln)
                unit = extract_unit(ln) or ref_match.get("expected_unit")
                
                # Standardize Reference Range
                ref_range = ref_match.get("reference")
                if isinstance(ref_range, dict): 
                    ref_range = ref_range.get(gender, list(ref_range.values())[0])
                elif isinstance(ref_range, list): 
                    ref_range = ref_range[0]
                
                # 🔥 FIX: Save directly under Date (No Section Folder)
                final["results"][date][canonical] = {
                    "value": valnum,
                    "unit": unit,
                    "reference_range": ref_range,
                    "status": status_from_value_and_ref(str(valnum) if valnum is not None else None, ref_range)
                }
                continue # Skip general insertion

            non_urine_refs = [r for r in reference_flat if "URINE" not in r["category"]]
            ref_match, score = pick_best_match_smart(name_candidate, ln, non_urine_refs, gender)
            
            if ref_match and score >= FUZZY_THRESHOLD:
                canonical = ref_match["original_name"]
                valnum = first_number(ln)
                unit = extract_unit(ln) or ref_match.get("expected_unit")
                
                # --- NEW LOGIC: Always pick the first range to save ---
                ref_range = ref_match.get("reference")
                if isinstance(ref_range, dict): 
                    ref_range = ref_range.get(gender, list(ref_range.values())[0])
                elif isinstance(ref_range, list): 
                    ref_range = ref_range[0] # FORCES it to use 12.5 - 14.5
                
                status = status_from_value_and_ref(str(valnum) if valnum is not None else None, ref_range)
                final["results"][date][canonical] = {
                    "value": valnum,
                    "unit": unit,
                    "reference_range": ref_range,
                    "status": status
                }
    OUTPUT_PATH.write_text(json.dumps(final, indent=2), encoding="utf-8")
    print("Saved final structured results to:", OUTPUT_PATH)

if __name__ == "__main__":
    main()