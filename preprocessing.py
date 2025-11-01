import pandas as pd
import re
import numpy as np
from typing import List, Dict, Any

class SpecialtyPreprocessor:
    def __init__(self, synonyms_file: str = 'medical_synonyms.csv'):
        """
        Initialize preprocessor with synonyms mapping
        
        Args:
            synonyms_file: Path to CSV file containing medical synonyms
        """
        self.synonyms_df = self.load_synonyms(synonyms_file)
        self.junk_patterns = self.initialize_junk_patterns()
        
    def load_synonyms(self, synonyms_file: str) -> pd.DataFrame:
        """Load synonyms from CSV file"""
        try:
            df = pd.read_csv(synonyms_file)
            # Sort by priority for ordered processing
            df = df.sort_values('priority')
            return df
        except FileNotFoundError:
            print(f"Warning: Synonyms file {synonyms_file} not found. Using default synonyms.")
            return self.create_default_synonyms()
    
    def create_default_synonyms(self) -> pd.DataFrame:
        """Create default synonyms if file not found"""
        default_data = {
            'type': ['abbreviation'] * 10,
            'pattern': ['ent', 'obgyn', 'gi', 'peds', 'psych', 'ortho', 'derm', 'neuro', 'cardio', 'uro'],
            'replacement': ['otolaryngology', 'obstetrics gynecology', 'gastroenterology', 'pediatrics', 
                          'psychiatry', 'orthopedic', 'dermatology', 'neurology', 'cardiology', 'urology'],
            'priority': [1] * 10
        }
        return pd.DataFrame(default_data)
    
    def initialize_junk_patterns(self) -> List[str]:
        """Initialize patterns for junk detection"""
        return [
            '####', '???', 'xyz', 'abc', 'tbd', 'temp', 'temporary', 
            'unknown', 'n/a', 'na', 'none', 'test', 'sample', 'random',
            'error', 'routine', 'med office', 'physician', 'dr', 'doctor'
        ]
    
    def safe_string_convert(self, text: Any) -> str:
        """
        Safely convert any input to string, handling NaN, None, and other types
        """
        if text is None:
            return ""
        elif pd.isna(text):
            return ""
        elif isinstance(text, (int, float)):
            return str(text)
        elif isinstance(text, str):
            return text
        else:
            return str(text)
    
    def normalize_text(self, text: Any) -> str:
        """
        Basic text normalization with safe type handling
        """
        # Safely convert to string first
        text_str = self.safe_string_convert(text)
        
        if not text_str:
            return ""
        
        # Convert to lowercase
        text_str = text_str.lower()
        
        # Remove extra whitespace
        text_str = ' '.join(text_str.split())
        
        # Remove punctuation except &, /, - (for compound terms)
        text_str = re.sub(r'[^\w\s&/-]', ' ', text_str)
        
        # Remove extra spaces again
        text_str = ' '.join(text_str.split())
        
        return text_str.strip()
    
    def is_junk_entry(self, text: str) -> bool:
        """
        Detect junk entries that should be filtered out
        """
        if not text or len(text.strip()) <= 2:
            return True
        
        # Check for junk patterns
        if any(pattern in text.lower() for pattern in self.junk_patterns):
            return True
        
        # Very short entries (1-2 chars) that aren't common abbreviations
        short_valid_abbr = ['ir', 'gi', 'ed', 'er', 'icu', 'picu', 'nicu']
        if len(text) <= 3 and text not in short_valid_abbr:
            return True
        
        # Contains only numbers or special characters
        if re.match(r'^[\d\W]+$', text):
            return True
        
        return False
    
    def apply_synonym_mapping(self, text: str) -> str:
        """
        Apply synonym mappings from CSV file with safe pattern handling
        """
        if not text:
            return ""
        
        processed_text = text
        
        # Apply replacements in priority order
        for _, row in self.synonyms_df.iterrows():
            pattern = self.safe_string_convert(row['pattern'])
            replacement = self.safe_string_convert(row['replacement'])
            mapping_type = self.safe_string_convert(row['type'])
            
            # Skip if pattern is empty after conversion
            if not pattern:
                continue
                
            try:
                if mapping_type in ['abbreviation', 'misspelling', 'short_form', 'professional_title', 'specialty_variation']:
                    # Word-level replacements (exact word matches)
                    processed_text = re.sub(r'\b' + re.escape(pattern) + r'\b', replacement, processed_text)
                
                elif mapping_type in ['phrase', 'variation']:
                    # Phrase-level replacements
                    processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
                
                elif mapping_type in ['department', 'professional_prefix', 'institutional']:
                    # Remove these terms entirely
                    processed_text = re.sub(r'\b' + re.escape(pattern) + r'\b', replacement, processed_text)
            
            except (re.error, TypeError) as e:
                # Fallback: simple string replacement for problematic patterns
                print(f"Warning: Regex error for pattern '{pattern}': {e}. Using string replacement.")
                processed_text = processed_text.replace(pattern, replacement)
        
        # Clean up extra spaces
        processed_text = ' '.join(processed_text.split())
        
        return processed_text.strip()
    
    def handle_special_cases(self, text: str) -> str:
        """
        Handle complex special cases and patterns
        """
        if not text:
            return ""
            
        special_cases = {
            r'ob\s*[/]?\s*gyn': 'obstetrics gynecology',
            r'psych\s*[/&]?\s*neuro': 'psychiatry neurology',
            r'heme\s*[/]?\s*onc': 'hematology oncology',
            r'pulm\s*[/]?\s*crit': 'pulmonary critical care',
            r'cardio\s*[/]?\s*thoracic': 'cardiothoracic',
            r'ortho\s*[/]?\s*trauma': 'orthopedic trauma',
        }
        
        processed_text = text
        for pattern, replacement in special_cases.items():
            try:
                processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
            except (re.error, TypeError) as e:
                print(f"Warning: Special case pattern error '{pattern}': {e}")
                continue
        
        return processed_text
    
    def split_multi_specialties(self, text: str) -> List[str]:
        """
        Split multi-specialty entries into individual specialties
        """
        if not text:
            return []
        
        # Common separators for multi-specialties
        separators = [r'/', r'&', r' and ', r',', r'\+']
        
        specialties = [text]
        
        for sep in separators:
            new_specialties = []
            for specialty in specialties:
                try:
                    if re.search(sep, specialty, re.IGNORECASE):
                        split_parts = re.split(sep, specialty, flags=re.IGNORECASE)
                        new_specialties.extend([part.strip() for part in split_parts if part.strip()])
                    else:
                        new_specialties.append(specialty)
                except (re.error, TypeError) as e:
                    print(f"Warning: Split error for '{specialty}' with separator '{sep}': {e}")
                    new_specialties.append(specialty)
            specialties = new_specialties
        
        return [s for s in specialties if s and len(s) > 2]
    
    def preprocess_specialty(self, raw_specialty: Any) -> List[str]:
        """
        Complete preprocessing pipeline for a single specialty entry
        
        Returns:
            List of processed specialty strings (empty list for junk entries)
        """
        # Step 1: Safely convert and normalize text
        normalized = self.normalize_text(raw_specialty)
        
        # Step 2: Check for junk
        if self.is_junk_entry(normalized):
            return []
        
        # Step 3: Handle special cases
        processed = self.handle_special_cases(normalized)
        
        # Step 4: Apply synonym mapping
        processed = self.apply_synonym_mapping(processed)
        
        # Step 5: Split multi-specialties
        specialties = self.split_multi_specialties(processed)
        
        # Step 6: Final cleaning and filtering
        final_specialties = []
        for specialty in specialties:
            # Remove any remaining junk
            if not self.is_junk_entry(specialty) and len(specialty) >= 3:
                # Final normalization
                cleaned = ' '.join(specialty.split())
                final_specialties.append(cleaned)
        
        return final_specialties
    
    def preprocess_dataframe(self, df: pd.DataFrame, specialty_column: str = 'raw_specialty') -> pd.DataFrame:
        """
        Preprocess an entire DataFrame of specialty entries
        
        Args:
            df: Input DataFrame
            specialty_column: Name of column containing raw specialties
            
        Returns:
            DataFrame with preprocessing results
        """
        results = []
        
        # Clean the input dataframe - handle NaN values in the specialty column
        df_clean = df.copy()
        df_clean[specialty_column] = df_clean[specialty_column].fillna('').astype(str)
        
        for idx, row in df_clean.iterrows():
            raw_specialty = row[specialty_column]
            
            # Preprocess
            processed_specialties = self.preprocess_specialty(raw_specialty)
            
            # Determine if junk
            is_junk = len(processed_specialties) == 0
            
            # Create result entry
            result = {
                'raw_specialty': raw_specialty,
                'processed_specialties': '|'.join(processed_specialties) if processed_specialties else '',
                'is_junk': is_junk,
                'specialty_count': len(processed_specialties)
            }
            
            results.append(result)
        
        return pd.DataFrame(results)

# Example usage and testing
def main():
    # Initialize preprocessor
    preprocessor = SpecialtyPreprocessor('medical_synonyms.csv')
    
    # Test with various input types including problematic ones
    test_cases = [
        "ENT",
        "OB/GYN Pain Management",
        "Peds Cardio",
        "GI Department",
        "Psych & Neuro",
        "Anesthesiology",
        "ABC",  # Junk
        "Dept of Ophthalmology",
        None,  # None value
        float('nan'),  # NaN value
        123,  # Number
        ""  # Empty string
    ]
    
    print("Testing preprocessing with various inputs:")
    for test in test_cases:
        result = preprocessor.preprocess_specialty(test)
        print(f"'{test}' -> {result}")
    
    # Example with DataFrame containing problematic values
    sample_data = pd.DataFrame({
        'raw_specialty': [
            'ENT',
            'OB/GYN',
            'Peds Cardiology',
            'GI Dept',
            'XYZ',  # Junk
            'Pain Management Clinic',
            None,  # None value
            float('nan'),  # NaN
            123,  # Number
            ''  # Empty string
        ]
    })
    
    processed_df = preprocessor.preprocess_dataframe(sample_data)
    print("\nProcessed DataFrame:")
    print(processed_df)

if __name__ == "__main__":
    main()