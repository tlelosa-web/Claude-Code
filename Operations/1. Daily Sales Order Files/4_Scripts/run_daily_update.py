
import datetime
import traceback
import sys
import update_sales_report
import generate_daily_summary

LOG_FILE = "1_Documentation\\USER_GUIDE.md"

def log_execution(status, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"- {timestamp}: {status} - {message}\n"
    
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read()
        
        lines = content.splitlines()
        header_indices = [
            i for i, line in enumerate(lines)
            if line.strip() in ("## Execution Log", "**Execution Log:**")
        ]

        if header_indices:
            insert_at = header_indices[0] + 1
            lines.insert(insert_at, log_entry.strip())
            new_content = "\n".join(lines) + "\n"
        else:
            suffix = "\n" if content.endswith("\n") else "\n\n"
            new_content = content + suffix + "## Execution Log\n" + log_entry.strip() + "\n"
            
        with open(LOG_FILE, "w") as f:
            f.write(new_content)
            
    except Exception as e:
        print(f"Warning: Could not update log file: {e}")

def main():
    print("=" * 60)
    print("DAILY SALES ORDER AUTOMATION - SELF-ANNEALING PROTOCOL")
    print("=" * 60)
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    print("Starting execution...")
    
    try:
        update_sales_report.main()
        print("\n" + "-" * 60)
        print("Generating Executive Summary...")
        generate_daily_summary.main()

        log_execution("SUCCESS", "Daily update completed successfully.")
        print("\n" + "=" * 60)
        print("EXECUTION SUCCESSFUL")
        print("=" * 60)

    except PermissionError:
        error_msg = "Excel file is locked. Please close it and try again."
        print("\n" + "!" * 60)
        print(error_msg)
        print("!" * 60)
        log_execution("BLOCKED", error_msg)
        sys.exit(1)

    except Exception as e:
        error_msg = f"Execution failed: {str(e)}"
        print("\n" + "!" * 60)
        print(error_msg)
        traceback.print_exc()
        print("!" * 60)
        log_execution("FAILURE", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
