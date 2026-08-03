import pandas as pd
import tempfile
import shutil
import os

out_path = r"5_Archive_and_Debug\debug_output_utf8.txt"

with open(out_path, "w", encoding="utf-8") as f:
    f.write("--- ItemListingReport.csv HEADERS ---\n")
    try:
        # Some CSVs from SAGE use latin1, we try utf-8-sig first
        try:
            df_csv = pd.read_csv(r"2_Source_Data\ItemListingReport.csv", nrows=5, encoding='utf-8-sig')
        except:
            df_csv = pd.read_csv(r"2_Source_Data\ItemListingReport.csv", nrows=5, encoding='latin1')
        f.write(str(df_csv.columns.tolist()) + "\n")
        f.write(str(df_csv.head(2)) + "\n")
    except Exception as e:
        f.write(f"Error reading CSV: {e}\n")

    f.write("\n--- Workshop Stock 19.03.26.xlsx HEADERS ---\n")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            temp_path = tmp.name
        shutil.copy2(r"2_Source_Data\Workshop Stock 19.03.26.xlsx", temp_path)
        df_xlsx = pd.read_excel(temp_path, nrows=5)
        f.write(str(df_xlsx.columns.tolist()) + "\n")
        f.write(str(df_xlsx.head(2)) + "\n")
        os.remove(temp_path)
    except Exception as e:
        f.write(f"Error reading XLSX: {e}\n")
