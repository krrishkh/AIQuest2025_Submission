import pandas as pd
from preprocessing import SpecialtyPreprocessor

def standardize_specialties(nucc_file: str, input_file: str, synonyms_file: str, output_file: str):
    """
    Main standardization function using the fixed preprocessor
    """
    try:
        # Load data
        nucc_df = pd.read_csv(nucc_file)
        input_df = pd.read_csv(input_file)
        
        # Initialize preprocessor
        preprocessor = SpecialtyPreprocessor(synonyms_file)
        
        # Preprocess specialties
        processed_df = preprocessor.preprocess_dataframe(input_df)
        
        # Now you can use the processed specialties for NUCC mapping
        # ... (your mapping logic here)
        
        # Save results
        processed_df.to_csv(output_file, index=False)
        print(f"Preprocessing complete. Results saved to {output_file}")
        
        return processed_df
        
    except Exception as e:
        print(f"Error in standardization: {e}")
        return None

# Run the standardization
standardize_specialties(
    nucc_file='nucc_taxonomy_master.csv',
    input_file='input_specialties.csv', 
    synonyms_file='medical_synonyms.csv',
    output_file='preprocessed_specialties.csv'
)