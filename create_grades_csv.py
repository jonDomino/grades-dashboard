"""
Create grades.csv from Live 2nd Halfs.xlsx

Output columns: date, dynamic, roto, game, type, bet, close, grade, col_c_original

Parsing rules:
- date: from col B (dates act as headers - all dates in 2025)
- dynamic, roto, game: parsed from col C pattern {dynamic} {roto} {game}
  - Example: "CFB 149 Ohio/Rutgers over 72 -115"
  - dynamic: "CFB" (first word)
  - roto: "149" (number after dynamic)
  - game: "Ohio/Rutgers" (stops when we see "over"/"under" or a number)
- type: "total" when over/under present, else "side"
- bet: col D (cit position) 
- close: col E (closing line)
- grade: for totals only - overs: close_line - bet_line, unders: bet_line - close_line
"""
import pandas as pd
import numpy as np
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("Creating grades.csv...")
print("="*80)

# Load file
df = pd.read_excel('Live 2nd Halfs.xlsx')
print(f"Loaded: {df.shape[0]} rows, {len(df.columns)} columns")

# Get columns by index
col_b = df.iloc[:, 1]  # Column B - dates as headers
col_c = df.iloc[:, 2]  # Column C - bet descriptions with {dynamic} {roto} {game}
col_d = df.iloc[:, 3]  # Column D - Cit Position (bet)
col_e = df.iloc[:, 4]  # Column E - Closing Line (close)

# Step 1: Build date mapping from Column B (dates appear as headers)
print("\n[1] Parsing dates from Column B...")
current_date = None
row_to_date = {}

for idx in range(len(col_b)):
    val = col_b.iloc[idx]
    
    # Check if this is a date
    if pd.notna(val) and isinstance(val, (pd.Timestamp, datetime)):
        current_date = pd.to_datetime(val).date()
        # Ensure year is 2025
        if current_date.year != 2025:
            current_date = current_date.replace(year=2025)
    
    # Assign current date to this row
    if current_date is not None:
        row_to_date[idx] = current_date

print(f"  Found date headers for {len(set(row_to_date.values()))} unique dates")
if row_to_date:
    dates_found = set(row_to_date.values())
    print(f"  Date range: {min(dates_found)} to {max(dates_found)}")

# Step 2: Parse Column C for dynamic, roto, game
print("\n[2] Parsing Column C for dynamic, roto, game...")

def parse_col_c(text):
    """
    Parse Column C text following pattern: {dynamic} {roto} {game}
    Example: "CFB 149 Ohio/Rutgers over 72 -115"
    - dynamic: "CFB" (first word)
    - roto: "149" (number after dynamic)
    - game: "Ohio/Rutgers" (stops when we see "over"/"under" or a number)
    """
    if pd.isna(text) or not isinstance(text, str):
        return None, None, None
    
    text = str(text).strip()
    
    # Skip empty or header rows
    if not text or text == "Cit Position":
        return None, None, None
    
    # Split into words
    words = text.split()
    if len(words) < 2:
        return None, None, None
    
    # First word is dynamic (e.g., "CFB", "CFBExtra")
    dynamic = words[0]
    
    # Second word should be roto (number)
    roto = None
    if len(words) >= 2:
        roto_match = re.match(r'^(\d{3,6})$', words[1])
        if roto_match:
            roto = roto_match.group(1)
    
    # Game is everything after roto until we see "over"/"under" or a number (which marks the end)
    game = None
    if roto and len(words) >= 3:
        game_parts = []
        for i in range(2, len(words)):
            word = words[i]
            # Stop when we see "over"/"under" or a number (like "72")
            if word.lower() in ['over', 'under']:
                break
            if re.match(r'^-?\d+\.?\d*$', word):  # Number pattern
                break
            game_parts.append(word)
        
        if game_parts:
            game = ' '.join(game_parts)
    
    return dynamic, roto, game

# Step 3: Extract line numbers from bet and close
print("\n[3] Extracting bet and close lines...")

def extract_line(text):
    """Extract the line number from text like '18.5 -122' or 'o20.5 -110'"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    text = str(text).strip()
    
    # Skip header rows
    if text in ["Cit Position", "Closing Line"]:
        return None
    
    # Remove o/u prefix if present
    text_clean = re.sub(r'^[ou]', '', text, flags=re.IGNORECASE)
    
    # Extract number before odds (could be like "18.5", "-7.5", ".5", "24")
    # Pattern: number, optional space, then odds like "-115" or "+105"
    match = re.search(r'(-?\d*\.?\d+)', text_clean)
    if match:
        try:
            return float(match.group(1))
        except:
            pass
    return None

def extract_juice(text):
    """Extract the juice (odds) from text like 'o73.5 -125' or '+6.5 +105'"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    text = str(text).strip()
    
    # Skip header rows
    if text in ["Cit Position", "Closing Line"]:
        return None
    
    # Find the juice pattern: +105, -110, -125, etc.
    # Look for +/- followed by digits (could be at end or before space)
    # Pattern: space or start, then +/- followed by digits
    match = re.search(r'(?:^|\s)([+-]\d+)(?:\s|$)', text)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    
    return None

def calculate_juice_difference(bet_juice, close_juice):
    """Calculate juice difference based on the formula:
    - When both negative: -125 - (-110) = -15 (direct subtraction)
    - When mixing positive/negative: normalize then subtract
      - bet +105, close -110: (105-100) - (-110+100) = 5 - (-10) = 15
      - bet -110, close +105: (-110+100) - (105-100) = -10 - 5 = -15
    """
    if bet_juice is None or close_juice is None:
        return 0
    
    # When both are negative, use direct subtraction
    if bet_juice < 0 and close_juice < 0:
        return bet_juice - close_juice
    
    # When mixing or both positive, normalize first
    # Normalize negative: add 100 to make it relative to 100
    # Normalize positive: subtract 100 to make it relative to 100
    if bet_juice < 0:
        bet_normalized = bet_juice + 100  # -110 becomes -10
    else:
        bet_normalized = bet_juice - 100  # +105 becomes 5
    
    if close_juice < 0:
        close_normalized = close_juice + 100  # -110 becomes -10
    else:
        close_normalized = close_juice - 100  # +105 becomes 5
    
    # Calculate difference: bet - close
    return bet_normalized - close_normalized

# Step 4: Build the grades dataframe
print("\n[4] Building grades dataframe...")

grades_data = []

for idx in range(len(df)):
    # Get date
    date = row_to_date.get(idx)
    
    # Get Column C text (bet description)
    col_c_val = col_c.iloc[idx] if idx < len(col_c) else None
    
    # Skip empty rows or header rows
    if pd.isna(col_c_val) or not isinstance(col_c_val, str):
        continue
    
    col_c_str = str(col_c_val).strip()
    if not col_c_str or col_c_str == "Cit Position":
        continue
    
    # Parse dynamic, roto, game from Column C
    dynamic, roto, game = parse_col_c(col_c_val)
    
    # Skip if we can't parse at least dynamic and roto
    if not dynamic or not roto:
        continue
    
    # Get bet line (Column D - cit position)
    col_d_val = col_d.iloc[idx] if idx < len(col_d) else None
    bet_text = str(col_d_val) if pd.notna(col_d_val) else ""
    
    # Skip header row
    if bet_text == "Cit Position":
        continue
    
    bet_line = extract_line(col_d_val)
    
    # Get close line (Column E - closing line)
    col_e_val = col_e.iloc[idx] if idx < len(col_e) else None
    close_text = str(col_e_val) if pd.notna(col_e_val) else ""
    
    # Skip header row
    if close_text == "Closing Line":
        continue
    
    close_line = extract_line(col_e_val)
    
    # Determine type - check for over/under in Column C or Column D
    type_val = "side"
    col_c_str_lower = col_c_str.lower()
    bet_text_lower = bet_text.lower()
    
    if 'over' in col_c_str_lower or 'under' in col_c_str_lower:
        type_val = "total"
    elif bet_text_lower.startswith('o') or bet_text_lower.startswith('u'):
        type_val = "total"
    
    # Extract juice from bet and close
    bet_juice = extract_juice(col_d_val)
    close_juice = extract_juice(col_e_val)
    
    # Calculate grade (only for totals for now)
    grade = None
    if type_val == "total" and bet_line is not None and close_line is not None:
        # Determine if over or under from bet text
        is_over = bet_text_lower.startswith('o') or 'over' in col_c_str_lower
        
        # Calculate line difference
        if is_over:
            line_diff = close_line - bet_line
        else:
            line_diff = bet_line - close_line
        
        # Multiply by 15 for line value
        line_value = line_diff * 15
        
        # Calculate juice adjustment
        juice_adjustment = calculate_juice_difference(bet_juice, close_juice)
        
        # Final grade = line value + juice adjustment
        grade = line_value + juice_adjustment
    
    # Only add if we have date and roto
    if date and roto:
        grades_data.append({
            'date': date,
            'dynamic': dynamic,
            'roto': roto,
            'game': game,
            'type': type_val,
            'bet': bet_text if bet_text != "Cit Position" else None,
            'close': close_text if close_text != "Closing Line" else None,
            'grade': grade,
            'col_c_original': col_c_val  # Original value from column C for inspection
        })

grades_df = pd.DataFrame(grades_data)
print(f"  Created {len(grades_df)} rows")

# Save to CSV
output_file = 'grades.csv'
grades_df.to_csv(output_file, index=False)
print(f"\n[5] Saved to {output_file}")

# Show sample
print("\nSample of grades.csv (first 10 rows):")
print(grades_df.head(10).to_string())

# Show statistics
print("\nStatistics:")
print(f"  Total rows: {len(grades_df)}")
print(f"  Rows with grades: {grades_df['grade'].notna().sum()}")
print(f"  Total bets: {(grades_df['type'] == 'total').sum()}")
print(f"  Side bets: {(grades_df['type'] == 'side').sum()}")

print("\n" + "="*80)
print("Done!")
