import os
import shutil

folders = [
    "1_Documentation",
    "2_Source_Data",
    "3_Live_Reports",
    "4_Scripts",
    "5_Archive_and_Debug"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Move the existing data files into 2_Source_Data
data_files = ["ItemListingReport.csv", "Workshop Stock 19.03.26.xlsx"]
for file in data_files:
    if os.path.exists(file):
        shutil.move(file, os.path.join("2_Source_Data", file))

# Initialize a basic RUN_PIPELINE.bat
with open("RUN_PIPELINE.bat", "w") as f:
    f.write("@echo off\n")
    f.write("echo Running Pipeline...\n")
    f.write("pause\n")

print("Scaffolding complete.")
