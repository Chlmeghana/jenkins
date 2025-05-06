import subprocess
import re
import sys
import csv
from openpyxl import Workbook

# Configuration
host = "gdlfcft.endicott.ibm.com"
user = sys.argv[1]
password = sys.argv[2]
filename = "PXBUCKET.H$$$"

def get_html_file(host, user, password, filename):
    command = f'lftp -u {user},{password} {host} -e "cat {filename}; bye"'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode("latin1")  # Use latin1 for encoding-safe decode

def parse_html(html):
    summary = {
        "Passed": 0,
        "Failed": 0,
        "Warnings": 0,
        "Errors": 0
    }
    passed = re.search(r'Tests Passed:\s*(\d+)', html)
    failed = re.search(r'Tests Failed:\s*(\d+)', html)
    warnings = re.findall(r'WARNING:', html)
    errors = re.findall(r'ERROR:', html)

    if passed:
        summary["Passed"] = int(passed.group(1))
    if failed:
        summary["Failed"] = int(failed.group(1))
    summary["Warnings"] = len(warnings)
    summary["Errors"] = len(errors)
    return summary

def remove_all_pre_blocks(html):
    # Remove all <pre>...</pre> blocks
    return re.sub(r'<pre>.*?</pre>', '', html, flags=re.DOTALL)

def write_summary_to_excel(summary, filename="test_summary.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Summary"
    ws.append(["Metric", "Count"])
    for key, value in summary.items():
        ws.append([key, value])
    wb.save(filename)

def write_summary_to_csv(summary, filename="test_summary.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Count"])
        for key, value in summary.items():
            writer.writerow([key, value])

def write_summary_to_html(html_content, filename="test_summary.html"):
    with open(filename, "w", encoding="latin1") as f:
        f.write(html_content)

# === Main Script Logic ===
html_content = get_html_file(host, user, password, filename)
cleaned_html = remove_all_pre_blocks(html_content)
summary = parse_html(html_content)

# Generate all report formats
write_summary_to_excel(summary)
write_summary_to_csv(summary)
write_summary_to_html(cleaned_html)

# Optional: Console output
print("Test Summary from HTML:", summary)
print("\n--- HTML Content Start ---\n")
print(cleaned_html.strip())
print("\n--- HTML Content End ---\n")
