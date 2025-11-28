# Grades Dashboard

Streamlit dashboard for analyzing bet correlation between risk amounts, grades, and results.

## Features

- **Risk vs Grade Analysis**: Interactive scatter plot with line of best fit and R² calculation
- **Risk Bucket Analysis**: Average grade by risk amount buckets with customizable bucket sizes
- **Dynamic Statistics**: Summary statistics grouped by dynamic (sport/league)
- **Advanced Filtering**: Filter by dynamic, date range, and risk amount range
- **Data Export**: Download filtered data and statistics as CSV

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have the required data files:
- `combined.csv` - Combined grades and results data

3. Run the dashboard:
```bash
streamlit run dashboard.py
```

## Data Requirements

The dashboard expects `combined.csv` with the following columns:
- `date`: Date of the bet
- `dynamic`: Sport/league identifier
- `roto`: Rotation number
- `grade`: Calculated grade value
- `risk`: Risk amount
- `result`: Result amount

The dashboard automatically:
- Removes rows where risk or grade is null
- Filters grades to the range [-30, 100]

## Usage

1. Use the sidebar filters to narrow down your analysis
2. View the Risk vs Grade scatter plot to see the correlation
3. Review risk bucket statistics to understand performance by bet size
4. Check dynamic statistics to compare performance across different sports/leagues
5. Export any filtered data or statistics using the download buttons

