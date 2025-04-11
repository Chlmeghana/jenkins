import subprocess
import re
import sys
import csv
from openpyxl import Workbook

# Configuration
host = "gdlfcft.endicott.ibm.com"
user = sys.argv[1]
password = sys.argv[2]
filename = sys.argv[3][:-5] + ".html"  # Trim .html or .HTML if needed

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

def write_summary_to_csv(summary, filename="test_summary.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Count"])
        for key, value in summary.items():
            writer.writerow([key, value])

def write_summary_to_html(summary, filename="test_summary.html"):
    html = f"""
    <html>
    <head>
        <title>Test Summary</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            table {{
                border-collapse: collapse;
                width: 50%;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h2>Test Summary Report</h2>
        <table>
            <tr><th>Metric</th><th>Count</th></tr>
            {''.join(f'<tr><td>{key}</td><td>{value}</td></tr>' for key, value in summary.items())}
        </table>
    </body>
    </html>
    """
    with open(filename, "w") as f:
        f.write(summary)

# === Main Script Logic ===
html_content = get_html_file(host, user, password, filename)
cleaned_html = remove_unwanted_pre_blocks(html_content)
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
