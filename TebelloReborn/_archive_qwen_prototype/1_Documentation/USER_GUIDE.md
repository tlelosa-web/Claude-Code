# User Guide

## Overview
This document provides instructions for human operators on how to use and maintain this project.

## Project Structure
- **1_Documentation/** - Project directives and guides
- **2_Source_Data/** - Raw input data files
- **3_Live_Reports/** - Generated outputs and dashboards
- **4_Scripts/** - Python automation scripts
- **5_Archive_and_Debug/** - Debug logs and obsolete files

## Getting Started
1. Place your source data files in `2_Source_Data/`
2. Add Python scripts to `4_Scripts/`
3. Run `RUN_PIPELINE.bat` to execute the full pipeline

## Running the Pipeline
- Double-click `RUN_PIPELINE.bat` from the Project Root
- Or run from terminal: `RUN_PIPELINE.bat`

## Troubleshooting
- Check `5_Archive_and_Debug/debug_output_utf8.txt` for detailed logs
- Ensure all paths are relative to the Project Root
