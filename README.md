# 🩺 Provider Specialty Standardization – HiLabs Hackathon 2025

## 📘 Project Overview
This project solves the **Provider Specialty Standardization** problem from **HiLabs Hackathon 2025**.  
The goal is to map unstructured, free-text provider specialties (e.g., `Cardio`, `OBGYN`, `Pain & Spine Doc`)  
to official **NUCC taxonomy codes**, producing standardized, high-quality data for U.S. healthcare systems.

Our Python tool:
- Cleans and preprocesses raw specialties.
- Handles typos, abbreviations, and noise.
- Uses **fuzzy matching** and **synonym expansion** to map to the most relevant NUCC taxonomy code(s).
- Flags ambiguous or meaningless entries as **JUNK**.

---

## 🧩 Input & Output

### **Input Files**
1. **`nucc_taxonomy_master.csv`**  
   Official NUCC taxonomy dataset containing columns:  
   `code, classification, specialization, display_name`

2. **`input_specialties.csv`**  
   Raw free-text list of provider specialties with one column:  
   `raw_specialty`

3. **`synonyms.csv`** *(optional but recommended)*  
   Custom dictionary mapping common abbreviations and slang to standardized terms.  
   Example:
   ```csv
   standard_term,alternate_terms
   otolaryngology,ent,ear nose throat
   obstetrics gynecology,obgyn,ob gyn,ob/gyn
   cardiology,cardio
   dermatology,derm
   endocrinology,endo
   ```

### **Output File**
**`output.csv`** containing:
| raw_specialty | nucc_codes | confidence | explain |
|----------------|-------------|-------------|----------|
| ANESTHESIOLOGY | 207L00000X | 0.95 | Exact match found for 'anesthesiology' |
| CARDIOLOGY | 207RC0000X | 0.87 | Close match (87% similarity) for 'cardiology' |
| DERMATOLOGY | 207N00000X | 0.9 | Exact match found for 'dermatology' |
| UNKNOWN FIELD | JUNK | 0.0 | Input classified as JUNK - no meaningful specialty detected |

---

## ⚙️ Command to Run

```bash
python main.py   --nucc nucc_taxonomy_master.csv   --input input_specialties.csv   --out output.csv   --synonyms synonyms.csv   
```

---

## 🧠 Major Debugging Journey

During development and testing, we encountered and resolved several **critical issues**.  
Below are the problems, their causes, and the implemented fixes.

---

### 🐞 1. **All Mappings Returned “JUNK”**
**Symptom:**  
Every specialty (even obvious ones like *Anesthesiology*) was being marked as `JUNK`.

**Root Cause:**  
The NUCC dataset column names were uppercase (`Code`, `Classification`, etc.),  
but our code expected lowercase (`code`, `classification`, `display_name`).

**Fix:**  
Normalized all column names to lowercase immediately after loading:
```python
df.columns = [c.strip().lower() for c in df.columns]
```

---

### 🧩 2. **KeyError: ['code'] not in index**
**Symptom:**  
Program crashed with `"['code'] not in index"` during fuzzy matching.

**Root Cause:**  
Because of inconsistent column names in NUCC DataFrame, the field `'code'` didn’t exist.

**Fix:**  
Aligned column references in preprocessing and matching functions to use lowercase consistently.

---

### ⚙️ 3. **No Matches – Threshold Too Strict**
**Symptom:**  
Fuzzy scores were being computed correctly (80–83%),  
but since the threshold was set to **85**, almost everything was rejected as low confidence.

**Fix:**  
Relaxed the fuzzy matching threshold to **70** and tuned confidence weighting.

---

### 🧹 4. **Error: `'float' object has no attribute 'strip'`**
**Symptom:**  
Script crashed mid-run on non-string inputs (like `NaN` or `123.0`).

**Root Cause:**  
`raw_specialty` values from CSV sometimes contained numeric or empty cells;  
`.strip()` was being called on a float.

**Fix:**  
Safely cast all inputs to strings in `preprocess_input()`.

---

## 🧾 5. **Errors Found in Input Raw File**

Before mapping, the raw input file `input_specialties.csv` had several **data quality issues** that caused misclassifications or crashes.

### **Types of Issues Observed**

| Type | Example | Problem | Fix Applied |
|------|----------|----------|-------------|
| **Missing / Blank Values** | (empty cell) | Caused preprocessing errors | Replaced with empty string and flagged as `JUNK` |
| **Numeric Entries** | `12345`, `4567.0` | Non-specialty numeric codes interpreted as float | Converted to string safely using `str()` |
| **Placeholder / Test Data** | `test`, `sample`, `unknown`, `zzz`, `tbd` | Meaningless or placeholder text | Identified using junk keyword list and flagged as `JUNK` |
| **Institution Names** | `ABC Hospital Cardiology Dept`, `XYZ Clinic` | Contained noise terms like *hospital*, *clinic* | Removed via regex-based noise filtering |
| **Abbreviations** | `OBGYN`, `ENT`, `DERM`, `CARDIO` | Could not match exactly to NUCC entries | Expanded using `synonyms.csv` mapping before fuzzy matching |
| **Mixed Case / Extra Spaces** | `  CardioLOGY  ` | Inconsistent formatting | Cleaned via `.lower()` and whitespace normalization |
| **Special Characters** | `Pain & Spine`, `Neuro/Ortho` | Symbols disrupted tokenization | Replaced `&`, `/`, `-` with spaces before matching |

---

### 🗂️ 6. **Synonyms Mapping Improvements**
**Purpose:**  
To standardize abbreviations and medical shorthand (e.g., ENT → Otolaryngology).

**Approach:**
- Created `synonyms.csv` manually from NUCC dataset patterns and medical slang.
- Each line contains one *standard term* and a list of comma-separated *alternate terms*.

---

## 🔍 Fuzzy Matching Logic Explained

Our mapping engine combines **token-based** and **partial ratio** fuzzy matching  
to handle partial overlaps, abbreviations, and typos.

### **1️⃣ Cleaning**
Both input and NUCC entries are cleaned:
- Lowercased  
- Punctuation removed  
- Common medical abbreviations expanded (OBGYN → Obstetrics Gynecology)

### **2️⃣ Matching**
```python
score = fuzz.token_set_ratio(cleaned_input, nucc_text)
```
- `token_set_ratio` ignores word order and focuses on overlap (ideal for multi-word phrases).
- Threshold = 70 ensures meaningful partial matches.

### **3️⃣ Confidence Scoring**
The best fuzzy score (0–100) is normalized to a 0–1 confidence range.

### **4️⃣ Decision Logic**
| Condition | Action |
|------------|---------|
| `confidence >= threshold` | Assign best matching NUCC code(s) |
| `confidence < threshold`  | Mark as `JUNK` |

### **5️⃣ Explanation Field**
Each output record includes a short rationale.

---

## 📈 Performance Summary
- Processed **10,000+ specialties** in under 15 minutes.


---

## 🏁 Credits
**Developed by:** *Team DeepSeek*  
**Hackathon:** HiLabs Hackathon 2025  
**Challenge:** Provider Specialty Standardization  
**Language:** Python 3.10+  
**Libraries Used:** pandas, fuzzywuzzy, regex, argparse, logging
