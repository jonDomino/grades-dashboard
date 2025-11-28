"""
Create combined.csv by joining grades.csv and results.csv

- Join on date and roto
- Filter for type = 'total' only
- Special roto matching: if rotos don't match but one is odd and other is even, 
  subtract 1 from even and check if they match
  - roto 101 (odd) matches with roto 102 (even) because 102-1=101
  - roto 102 (even) does NOT match with roto 103 (odd)
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("Creating combined.csv from grades.csv and results.csv...")
print("="*80)

# Load both CSV files
print("\n[1] Loading CSV files...")
grades_df = pd.read_csv('grades.csv')
results_df = pd.read_csv('results.csv')

print(f"  Grades: {len(grades_df)} rows")
print(f"  Results: {len(results_df)} rows")

# Include both totals and sides
print("\n[2] Processing all bet types...")
grades_all = grades_df.copy()
print(f"  Total bets in grades: {len(grades_all)} rows")
print(f"    - Totals: {len(grades_all[grades_all['type'] == 'total'])} rows")
print(f"    - Sides: {len(grades_all[grades_all['type'] == 'side'])} rows")

# Convert date columns to same type for joining
grades_all['date'] = pd.to_datetime(grades_all['date']).dt.date
results_df['date'] = pd.to_datetime(results_df['date']).dt.date

# Convert roto to int for matching
grades_all['roto'] = grades_all['roto'].astype(str).str.strip()
results_df['roto'] = results_df['roto'].astype(str).str.strip()

def roto_match(roto1, roto2):
    """
    Check if two rotos match, with special logic:
    - Direct match
    - OR if one is odd and one is even, subtract 1 from even and check if equals odd
      - roto 101 (odd) matches with roto 102 (even) because 102-1=101
      - roto 102 (even) does NOT match with roto 103 (odd)
    Works both directions: 101↔102 and 102↔101 both match
    """
    try:
        r1 = int(roto1)
        r2 = int(roto2)
        
        # Direct match
        if r1 == r2:
            return True
        
        # Check if one is odd and one is even, and even-1 equals odd
        if r1 % 2 == 0 and r2 % 2 == 1:  # r1 is even, r2 is odd
            if r1 - 1 == r2:
                return True
        elif r1 % 2 == 1 and r2 % 2 == 0:  # r1 is odd, r2 is even
            if r2 - 1 == r1:
                return True
        
        return False
    except:
        return False

print("\n[3] Joining grades and results with special roto matching...")

# Perform the join with special roto matching logic
combined_data = []

for _, grade_row in grades_all.iterrows():
    grade_date = grade_row['date']
    grade_roto = str(grade_row['roto'])
    
    # Find matching results
    matching_results = results_df[
        (results_df['date'] == grade_date)
    ]
    
    for _, result_row in matching_results.iterrows():
        result_roto = str(result_row['roto'])
        
        # Check if rotos match (with special logic)
        if roto_match(grade_roto, result_roto):
            # Combine the rows
            combined_row = grade_row.copy()
            combined_row['risk'] = result_row['risk']
            combined_row['result'] = result_row['result']
            combined_data.append(combined_row)
            break  # Found a match, move to next grade row

combined_df = pd.DataFrame(combined_data)
print(f"  Matched {len(combined_df)} rows")

# Select the columns we want in the final output
# Include all grade columns plus risk and result from results
# Excluded: roto, game, col_c_original
output_columns = [
    'date', 'dynamic', 'type', 'bet', 'close', 
    'grade', 'risk', 'result'
]

# Only include columns that exist
final_columns = [col for col in output_columns if col in combined_df.columns]
combined_df = combined_df[final_columns]

# Save to CSV
output_file = 'combined.csv'
combined_df.to_csv(output_file, index=False)
print(f"\n[4] Saved to {output_file}")

# Show sample
print("\nSample of combined.csv (first 10 rows):")
print(combined_df.head(10).to_string())

# Show statistics
print("\nStatistics:")
print(f"  Total matched rows: {len(combined_df)}")
print(f"  Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
if 'risk' in combined_df.columns and 'result' in combined_df.columns:
    print(f"  Total risk: ${combined_df['risk'].sum():.2f}")
    print(f"  Total result: ${combined_df['result'].sum():.2f}")
    if combined_df['grade'].notna().any():
        print(f"  Rows with grades: {combined_df['grade'].notna().sum()}")

print("\n" + "="*80)
print("Done!")

