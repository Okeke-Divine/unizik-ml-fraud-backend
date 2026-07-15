# unizik-ml-fraud-backend/app/data_generator.py

import os
import sys
import numpy as np
import pandas as pd

# Ensure the root project directory is in the Python path when executed directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config import Config

def generate_unizik_dataset() -> pd.DataFrame:
    # 1. Initialize random seed for absolute academic reproducibility
    np.random.seed(42)
    
    print("Initializing synthetic data generation pipeline...")
    
    # 2. Generate Class 0: Legitimate Student Transactions (3,500 rows)
    n_legit = 3500
    legit_data = {
        'device_student_count_24h': np.random.choice([1, 2], size=n_legit, p=[0.85, 0.15]),
        'page_dwell_time_seconds': np.round(np.random.normal(loc=65.0, scale=25.0, size=n_legit), 1),
        'is_high_risk_asn': np.zeros(n_legit, dtype=int),
        'failed_attempts_1h': np.random.choice([0, 1], size=n_legit, p=[0.90, 0.10]),
        'session_hardware_mismatch': np.zeros(n_legit, dtype=int),
        'is_off_peak_hour': np.random.choice([0, 1], size=n_legit, p=[0.95, 0.05]),
        'target_label': np.zeros(n_legit, dtype=int)
    }
    
    # Ensure dwell times remain within realistic human reading boundaries (25.0s to 180.0s)
    legit_data['page_dwell_time_seconds'] = np.clip(legit_data['page_dwell_time_seconds'], 25.0, 180.0)
    df_legit = pd.DataFrame(legit_data)
    
    # 3. Generate Class 1: Fraudulent / Cybercafe Proxy Transactions (1,500 rows)
    n_fraud = 1500
    fraud_data = {
        'device_student_count_24h': np.random.randint(low=5, high=35, size=n_fraud),
        'page_dwell_time_seconds': np.round(np.random.uniform(low=1.5, high=8.0, size=n_fraud), 1),
        'is_high_risk_asn': np.random.choice([0, 1], size=n_fraud, p=[0.30, 0.70]),
        'failed_attempts_1h': np.random.randint(low=2, high=8, size=n_fraud),
        'session_hardware_mismatch': np.random.choice([0, 1], size=n_fraud, p=[0.20, 0.80]),
        'is_off_peak_hour': np.random.choice([0, 1], size=n_fraud, p=[0.40, 0.60]),
        'target_label': np.ones(n_fraud, dtype=int)
    }
    df_fraud = pd.DataFrame(fraud_data)
    
    # 4. Inject Anti-Bias Legitimate Edge Cases (150 rows)
    # Represents students sharing laptops in lodges/cafes with normal reading dwell speeds and clean ASNs
    n_edge = 150
    edge_data = {
        'device_student_count_24h': np.random.randint(low=2, high=5, size=n_edge),
        'page_dwell_time_seconds': np.round(np.random.uniform(low=40.0, high=120.0, size=n_edge), 1),
        'is_high_risk_asn': np.zeros(n_edge, dtype=int),
        'failed_attempts_1h': np.random.choice([0, 1], size=n_edge, p=[0.80, 0.20]),
        'session_hardware_mismatch': np.zeros(n_edge, dtype=int),
        'is_off_peak_hour': np.random.choice([0, 1], size=n_edge, p=[0.85, 0.15]),
        'target_label': np.zeros(n_edge, dtype=int)
    }
    df_edge = pd.DataFrame(edge_data)
    
    # 5. Concatenate, shuffle random row order, and reset index
    df_full = pd.concat([df_legit, df_fraud, df_edge], ignore_index=True)
    df_shuffled = df_full.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    return df_shuffled

def run_pipeline():
    df = generate_unizik_dataset()
    
    # Ensure export directory exists
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    export_path = os.path.join(Config.DATA_DIR, 'unizik_transactions.csv')
    
    # Export to CSV without index column
    df.to_csv(export_path, index=False)
    
    print("\n" + "="*60)
    print("UNIZIK SYNTHETIC TRANSACTION MATRIX GENERATED SUCCESSFULLY")
    print("="*60)
    print(f"File Exported To : {export_path}")
    print(f"Total Records    : {len(df):,}")
    print(f"Legitimate (0)   : {len(df[df['target_label'] == 0]):,} rows ({len(df[df['target_label'] == 0])/len(df)*100:.1f}%)")
    print(f"Fraudulent (1)   : {len(df[df['target_label'] == 1]):,} rows ({len(df[df['target_label'] == 1])/len(df)*100:.1f}%)")
    print("="*60)
    print("\nFeature Class Averages (Validation Check):")
    print(df.groupby('target_label').mean().round(2))
    print("="*60 + "\n")

if __name__ == '__main__':
    run_pipeline()