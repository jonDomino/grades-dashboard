"""
Create results.csv from Rampage Live 2025.xlsx

Output columns: date, dynamic, roto, risk, result

Just extract and rename existing columns - no parsing needed.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("Creating results.csv from Rampage Live 2025.xlsx...")
print("="*80)

# Load file
df = pd.read_excel('Rampage Live 2025.xlsx')
print(f"Loaded: {df.shape[0]} rows, {len(df.columns)} columns")

# Clean column names (remove whitespace)
df.columns = df.columns.str.strip()

print(f"\nAvailable columns: {list(df.columns)}")

# Extract the columns we need
results_df = pd.DataFrame()

# Date - convert to date only (remove time)
results_df['date'] = pd.to_datetime(df['Date']).dt.date

# Dynamic
results_df['dynamic'] = df['Dynamic']

# Roto (Game #)
results_df['roto'] = df['Game #']

# Risk
results_df['risk'] = df['Risk']

# Result
results_df['result'] = df['Result\n(Automated)']

print(f"\nExtracted {len(results_df)} rows")

# Show sample
print("\nSample of results.csv (first 10 rows):")
print(results_df.head(10).to_string())

# Save to CSV
output_file = 'results.csv'
results_df.to_csv(output_file, index=False)
print(f"\nSaved to {output_file}")

# Show statistics
print("\nStatistics:")
print(f"  Total rows: {len(results_df)}")
print(f"  Date range: {results_df['date'].min()} to {results_df['date'].max()}")
print(f"  Unique rotations: {results_df['roto'].nunique()}")
print(f"  Total risk: ${results_df['risk'].sum():.2f}")
print(f"  Total result: ${results_df['result'].sum():.2f}")

print("\n" + "="*80)
print("Done!")

