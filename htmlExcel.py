import subprocess
import re
import sys
import re
from openpyxl import Workbook

# Configuration
host = "gdlfcft.endicott.ibm.com"
user = sys.argv[1]
password = sys.argv[2]
filename = sys.argv[3][:-5]+".html"  # e.g. CFTDEMOT.html -> CFTDEMOT.html

def get_html_file(host, user, password, filename):
    command = f'lftp -u {user},{password} {host} -e "cat {filename}; bye"'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode("latin1")  # Handle non-UTF8 characters safely

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

def remove_unwanted_pre_blocks(html):
    pattern = r'<pre>.*?HCPCFC015E Command not valid before LOGON: ID.*?</pre>'
    return re.sub(pattern, '', html, flags=re.DOTALL)

def write_summary_to_excel(summary, filename="test_summary.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Summary"
    ws.append(["Metric", "Count"])

    for key, value in summary.items():
        ws.append([key, value])

    wb.save(filename)

# Main logic
html_content = get_html_file(host, user, password, filename)
summary = parse_html(html_content)
cleaned_html = remove_unwanted_pre_blocks(html_content)

# Save Excel
write_summary_to_excel(summary)

# Output for console/log
print("Test Summary from HTML:", summary)
print("\n--- HTML Content Start ---\n")
print(cleaned_html.strip())
print("\n--- HTML Content End ---\n")
