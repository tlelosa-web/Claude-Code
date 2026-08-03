import pdfplumber
import re
import os

# This is the directory where the PDF files are stored.
# Make sure this path is correct.
RELEASED_JOBS_DIR = r"C:\Users\Fan Movement\OneDrive - Fan Movement (Pty) Ltd\Zinziso Xhallie's files - Sales\Sales Contracts & Register\Contract Register\Released Jobs"

def extract_payment_status_from_comments(pdf_path):
    """
    Scans PDF comments (annotations) for payment status.
    This is considered the primary source of truth.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                if page.annots:
                    for annot in page.annots:
                        # Annotations of subtype 'Text' are usually user comments.
                        if annot.get('subtype') == 'Text' and annot.get('contents'):
                            comment_text = annot.get('contents', '').upper()
                            # Check for the key phrases.
                            if "CASH SALE" in comment_text or "ACCOUNT" in comment_text:
                                # Return the first line of the comment, cleaned up.
                                return comment_text.splitlines()[0].strip()
        return None # No relevant comment found
    except Exception as e:
        return f"Error reading comments: {e}"

def extract_payment_status_from_text(pdf_path):
    """
    Scans the visible text of a PDF for payment status keywords.
    This is the fallback method.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                # Use a small tolerance to correctly read table-like structures.
                text += page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            
            text_upper = text.upper()

            # A list of the most specific phrases to search for, in order of preference.
            EXPLICIT_PHRASES = [
                "CASH SALE - PAID", "CASH SALE - UNPAID", "CASH SALE - PARTIAL",
                "ACCOUNT - UP TO DATE", "ACCOUNT - OUTSTANDING"
            ]
            for phrase in EXPLICIT_PHRASES:
                if phrase in text_upper:
                    return phrase

            # Fallback to broader terms if no explicit phrase is found.
            if "CASH SALE" in text_upper:
                return "CASH SALE (from text)"
            if "ACCOUNT" in text_upper:
                # This was the problem area, defaulting to "UP TO DATE".
                # Now it returns a more generic status to show it's from text.
                return "ACCOUNT (from text)"

            return "No status found in text"
    except Exception as e:
        return f"Error reading text: {e}"

def get_payment_status(pdf_path):
    """
    Main function to get payment status. It tries comments first, then text.
    """
    print(f"\n--- Checking: {os.path.basename(pdf_path)} ---")
    
    # 1. Try to get status from comments.
    comment_status = extract_payment_status_from_comments(pdf_path)
    if comment_status and "Error" not in comment_status:
        print(f"  [SUCCESS] Found in comments: '{comment_status}'")
        return comment_status
    else:
        print("  [INFO] No relevant status found in comments.")

    # 2. If no comment status, fall back to text extraction.
    text_status = extract_payment_status_from_text(pdf_path)
    print(f"  [INFO] Fallback to text scan result: '{text_status}'")
    
    return text_status


def dump_pdf_content(pdf_path, output_file):
    """
    Dumps all extracted text and annotation content from a PDF to a text file.
    """
    print(f"--- Dumping content of {os.path.basename(pdf_path)} to {output_file} ---")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            with pdfplumber.open(pdf_path) as pdf:
                f.write("=== ANNOTATIONS ===\n")
                found_annots = False
                for i, page in enumerate(pdf.pages):
                    if page.annots:
                        found_annots = True
                        f.write(f"\n--- Page {i+1} Annotations ---\n")
                        for annot in page.annots:
                            f.write(f"{annot}\n")
                if not found_annots:
                    f.write("No annotations found.\n")

                f.write("\n\n=== EXTRACTED TEXT ===\n")
                for i, page in enumerate(pdf.pages):
                    f.write(f"\n--- Page {i+1} Text ---\n")
                    text = page.extract_text(x_tolerance=1, y_tolerance=3)
                    f.write(text if text else "No text found on this page.")
        print(f"  [SUCCESS] Dump complete.")
    except Exception as e:
        print(f"  [ERROR] Failed to dump PDF content: {e}")


if __name__ == "__main__":
    # The PDF to investigate
    pdf_to_debug = "FM3589 - Cash Sale - Sales Order - SO4130.pdf"
    output_debug_file = "debug_output.txt"
    
    full_path = os.path.join(RELEASED_JOBS_DIR, pdf_to_debug)

    if os.path.exists(full_path):
        dump_pdf_content(full_path, output_debug_file)
    else:
        print(f"--- File not found: {pdf_to_debug} ---")
