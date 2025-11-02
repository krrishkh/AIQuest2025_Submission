## NOTE : Consider Hilab Hackthon Notebook as Best solution ( output file -> output_notebook )


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

## Solutions --->

The major issue was to tackle the input speciality to convert this to a meaningfull word so that we can map to the standardize nucc code.
We found the following type of errors ->

1. SPELLING ERRORS & TYPOS
Simple misspellings: PED1ATR1CS, CL1N1CAL, PHYS1CAL MED1C1NE

Character substitutions: 0B/GYN (zero instead of O), 1nternal Medicine (1 instead of I)

Missing characters: Anesthe (incomplete), Nephr (truncated)

Extra characters: PHYSICAL THERAPY & REHAB (double space)

2. ABBREVIATIONS & ACRONYMS
Common medical: ENT, OB/GYN, PCP, NP, PA, CRNA

Specialty-specific: ABA (Applied Behavioral Analysis), MOHS (Micrographic Surgery)

Departmental: IR (Interventional Radiology), IP (Inpatient)

3. SYNONYMS & ALTERNATIVE PHRASINGS
Word order variations: Internal Medicine vs Medicine, Internal

Different terminology: Family Practice vs Family Medicine

With/without hyphens: Speech Language Pathologist vs Speech-Language Pathologist

4. MULTI-SPECIALTY COMBINATIONS
Slash-separated: HEMATOLOGY/ONCOLOGY, PEDIATRIC HEMATOLOGY/ONCOLOGY

Ampersand combinations: OBSTETRICS & GYNECOLOGY

Multiple specialties: FAMILY MEDICINE WITH OBSTETRICS & PEDIATRICS

5. NOISE WORDS & IRRELEVANT TEXT
Department labels: Dept of Ophthalmology, Cardiology hospital, Pain Management CLINIC

Geographic references: - USA, Pathology - USA

Program/service labels: Program, Service, Center, Division, Unit

6. FORMATTING INCONSISTENCIES
Case variations: CARDIOLOGY (all caps) vs Cardiology (proper case) vs cardiology (lowercase)

Parentheses usage: PSYCHIATRY (CHILD & ADOLESCENT) vs PSYCHIATRY CHILD & ADOLESCENT

Special characters: OB/GYN vs OBSTETRICS & GYNECOLOGY

7. JUNK & NON-SPECIALTY ENTRIES
Placeholders: tbd, temporary, UNKNOWN, N/A, ####, xyz, abc clinic

Transportation: TAXI, AMBULANCE, DRIVER

Administrative: CONTRACTOR, AGENCY, PUBLIC SECTOR, NON-COVERED SPECIALTY

8. PARTIAL/INCOMPLETE TERMS
Truncated entries: Cardio, Anesthe, Orthopedi, Gastroen

Incomplete phrases: AND METABOLISM - 207RE0101X (missing specialty)

9. TAXONOMY CODE REFERENCES
Direct code mentions: CARDIOLOGY - 207RC0000X, ADULT - 364SP0809X

Code-only entries: 207L00000X, 208600000X

10. SPECIAL CHARACTER & ENCODING ISSUES
Encoding problems: PSYCHOLOGY Ã¢â‚¬â€œ PEDIATRIC (corrupted characters)

Ampersand variations: & vs &amp; (HTML entities)

Unicode issues: OCCUPATIONAL THERAPIST ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ HAND

11. QUALIFIERS & MODIFIERS
Staff/level indicators: - STAFF, - Physician, - Nurse Practitioner

Practice types: - PCP, - NON-PAR ONLY, - BOARD CERTIFIED

Setting modifiers: - HOSPITAL, - CLINIC, - OUTPATIENT

12. DUPLICATES WITH MINOR VARIATIONS
Spacing differences: ADDICTION MEDICINE vs ADDICTIONMEDICINE

Punctuation: PAIN MANAGEMENT vs PAINMANAGEMENT

Word forms: CHIROPRACTOR vs CHIROPRACTIC

13. DOMAIN-SPECIFIC JARGON
Medical slang: ENT (Ear, Nose, Throat), OB/GYN (Obstetrics/Gynecology)

Technical terms: MOHS-MICROGRAPHIC (surgery type)

Procedure-based: APPLIED BEHAVIORAL ANALYSIS (ABA)

14. COMBINED SPECIALTIES WITH PARENTHESES
Subspecialty clarifications: PSYCHIATRY (CHILD & ADOLESCENT)

Focus areas: NEUROLOGY (SPECIALIST)

Multiple certifications: NURSE PRACTITIONER (FAMILY)

15. INSTITUTIONAL & DEPARTMENTAL ENTRIES
Hospital departments: EMERGENCY DEPARTMENT, RADIOLOGY DEPARTMENT

Clinic types: URGENT CARE CLINIC, COMMUNITY HEALTH CENTER

Program names: HOSPICE PROGRAM, BEHAVIORAL HEALTH CLINIC

16. NON-STANDARD CAPITALIZATION
Mixed case: Addiction Medicine vs ADDICTION MEDICINE

Title case variations: Family Medicine vs FAMILY MEDICINE

Random capitalization: Dr. Internal Medicine

17. MEASUREMENT & SERVICE UNITS
Support services: NUTRITIONAL COUNSELING, SOCIAL WORK SERVICES

Therapy types: PHYSICAL THERAPY, OCCUPATIONAL THERAPY

Diagnostic services: LABORATORY, IMAGING CENTER

18. LEGACY & DEPRECATED TERMS
Old terminology: GENERAL PRACTICE (less common now)

Historical names: Various outdated specialty designations

19. HYBRID & COMPOUND SPECIALTIES
Combined fields: INTERVENTIONAL CARDIOLOGY, PEDIATRIC NEUROLOGY

Cross-disciplinary: MEDICAL GENETICS, SPORTS MEDICINE

20. LANGUAGE & LOCAL VARIATIONS
British vs American: PAEDIATRICS vs PEDIATRICS

Regional preferences: Different naming conventions by healthcare system



## ---> We have prepared a **preprocessing class** and **synonyms.csv** to tackle the preprocessing step.


## Two Soloutions ->
   1. We have created a python Notebook Hilabs Hackathon (Uses preprocessing) -> output : output_notebook** (best submission)**
   2. main.py also uses a different logic but preprocessing is same -> output : output 
   


## ⚙️ Command to Run (For main.py)

```bash
python main.py   --nucc nucc_taxonomy_master.csv   --input input_specialties.csv   --out output.csv   --synonyms synonyms.csv   
```

---



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

### **Synonyms Mapping Improvements**
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





