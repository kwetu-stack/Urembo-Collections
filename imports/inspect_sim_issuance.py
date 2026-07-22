import pandas as pd

FILE = "data/raw/1140749_SIM Insuance and Utilization Report as of_07-05-2026.xlsx"

xls = pd.ExcelFile(FILE)

print("\n==============================")
print("WORKBOOK INFORMATION")
print("==============================")

print(f"Sheets: {xls.sheet_names}")

for sheet in xls.sheet_names:

    print("\n----------------------------------")
    print(f"Sheet: {sheet}")
    print("----------------------------------")

    df = pd.read_excel(FILE, sheet_name=sheet)

    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\nFirst 10 rows:\n")

    print(df.head(10))
    print("\nCOLUMN NAMES:")
for i, col in enumerate(df.columns, start=1):
    print(f"{i}. {col}")