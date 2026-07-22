from pathlib import Path
import pandas as pd

# ==========================================================
# TUDOR AGENTS WORKBOOK INSPECTION
# ==========================================================

# Path to the Excel file
file_path = Path("data/raw/TUDOR AGENTS.xlsx")

print("=" * 60)
print("TUDOR AGENTS WORKBOOK INSPECTION")
print("=" * 60)

# ----------------------------------------------------------
# Check that the file exists
# ----------------------------------------------------------

if not file_path.exists():
    print(f"\nERROR: File not found:\n{file_path}")
    exit()

# ----------------------------------------------------------
# Read workbook information
# ----------------------------------------------------------

excel_file = pd.ExcelFile(file_path)

print("\nWorkbook:")
print(file_path.name)

print("\nSheets:")
for sheet in excel_file.sheet_names:
    print(f" - {sheet}")

# ----------------------------------------------------------
# Read without headers so we can inspect the raw workbook
# ----------------------------------------------------------

raw_df = pd.read_excel(file_path, header=None)

print("\nTotal Rows :", len(raw_df))
print("Total Columns :", len(raw_df.columns))

print("\nFirst 6 Raw Rows:")
print(raw_df.head(6))

# ----------------------------------------------------------
# Automatically detect the header row
# ----------------------------------------------------------

header_row = None

for i in range(min(10, len(raw_df))):
    first_cell = str(raw_df.iloc[i, 0]).strip().upper()

    if first_cell == "AGENT":
        header_row = i
        break

if header_row is None:
    print("\nERROR: Could not locate the header row.")
    exit()

print(f"\nHeader row detected at Excel row: {header_row + 1}")

# ----------------------------------------------------------
# Build a clean dataframe using the detected header
# ----------------------------------------------------------

df = pd.read_excel(file_path, header=header_row)

print("\nColumn Names:")
for i, col in enumerate(df.columns, start=1):
    print(f"{i}. {col}")

print("\nData Types:")
print(df.dtypes)

print("\nFirst 5 Records:")
print(df.head())

print("\nTotal Agent Records:", len(df))

print("\nInspection Complete.")
print("=" * 60)