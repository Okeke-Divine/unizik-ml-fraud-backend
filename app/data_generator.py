# unizik-ml-fraud-backend/app/data_generator.py

import os
import sys
import numpy as np
import pandas as pd

# Ensure the root project directory is in the Python path when executed directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.config import Config

def generate_unizik_dataset() -> pd.DataFrame:
    # Initialize random seed for academic reproducibility
    np.random.seed(42)
    
    print("Initializing synthetic data generation pipeline with realistic statistical noise...")
    
    # 1. Generate Class 0: Legitimate Student Transactions (3,500 rows)
    n_legit = 3500
    legit_data = {
        # Legitimate students mostly use 1 device, but can share up to 4 (e.g. in lodges)
        'device_student_count_24h': np.random.choice([1, 2, 3, 4], size=n_legit, p=[0.75, 0.15, 0.07, 0.03]),
        # Dwell time averages 65s, but can be as fast as 12s for returning users
        'page_dwell_time_seconds': np.round(np.random.normal(loc=65.0, scale=25.0, size=n_legit), 1),
        # Standard student traffic uses clean local ISP networks
        'is_high_risk_asn': np.zeros(n_legit, dtype=int),
        # Legitimate students face network errors/declines, allowing up to 3 failures
        'failed_attempts_1h': np.random.choice([0, 1, 2, 3], size=n_legit, p=[0.70, 0.20, 0.07, 0.03]),
        'session_hardware_mismatch': np.random.choice([0, 1], size=n_legit, p=[0.98, 0.02]),
        'is_off_peak_hour': np.random.choice([0, 1], size=n_legit, p=[0.94, 0.06]),
        'target_label': np.zeros(n_legit, dtype=int)
    }
    
    # Clip continuous boundaries to human constraints
    legit_data['page_dwell_time_seconds'] = np.clip(legit_data['page_dwell_time_seconds'], 12.0, 180.0)
    df_legit = pd.DataFrame(legit_data)
    
    # 2. Generate Class 1: Fraudulent / Cybercafe Proxy Transactions (1,500 rows)
    n_fraud = 1500
    fraud_data = {
        # Cybercafe operators process many accounts, but some cautious ones process as few as 3 to evade detection
        'device_student_count_24h': np.random.randint(low=3, high=35, size=n_fraud),
        # Script velocity is rapid, but manual card copiers might take up to 22 seconds
        'page_dwell_time_seconds': np.round(np.random.uniform(low=1.5, high=22.0, size=n_fraud), 1),
        # Fraudsters favor VPNs/Datacenters, but 25% of the time they use compromised local consumer ISP sims
        'is_high_risk_asn': np.random.choice([0, 1], size=n_fraud, p=[0.25, 0.75]),
        # Some stolen cards work on first try (0 fails), while card-testers generate multiple failures
        'failed_attempts_1h': np.random.choice([0, 1, 2, 3, 4, 5, 6], size=n_fraud, p=[0.10, 0.15, 0.25, 0.20, 0.15, 0.10, 0.05]),
        'session_hardware_mismatch': np.random.choice([0, 1], size=n_fraud, p=[0.25, 0.75]),
        'is_off_peak_hour': np.random.choice([0, 1], size=n_fraud, p=[0.40, 0.60]),
        'target_label': np.ones(n_fraud, dtype=int)
    }
    df_fraud = pd.DataFrame(fraud_data)
    
    # 3. Generate Anti-Bias Edge Cases (150 rows)
    n_edge = 150
    edge_data = {
        'device_student_count_24h': np.random.randint(low=2, high=5, size=n_edge),
        'page_dwell_time_seconds': np.round(np.random.uniform(low=30.0, high=120.0, size=n_edge), 1),
        'is_high_risk_asn': np.zeros(n_edge, dtype=int),
        'failed_attempts_1h': np.random.choice([0, 1, 2], size=n_edge, p=[0.60, 0.30, 0.10]),
        'session_hardware_mismatch': np.zeros(n_edge, dtype=int),
        'is_off_peak_hour': np.random.choice([0, 1], size=n_edge, p=[0.85, 0.15]),
        'target_label': np.zeros(n_edge, dtype=int)
    }
    df_edge = pd.DataFrame(edge_data)
    
    # 4. Concatenate, shuffle, and reset index
    df_full = pd.concat([df_legit, df_fraud, df_edge], ignore_index=True)
    df_shuffled = df_full.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    return df_shuffled

def run_pipeline():
    df = generate_unizik_dataset()
    
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    export_path = os.path.join(Config.DATA_DIR, 'unizik_transactions.csv')
    df.to_csv(export_path, index=False)
    
    print("\n" + "="*60)
    print("UNIZIK TRANSACTION MATRIX GENERATED WITH REALISTIC OVERLAP")
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