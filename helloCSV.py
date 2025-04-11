import subprocess
import re
import sys
import csv

# Configuration
host = "gdlfcft.endicott.ibm.com"
user = sys.argv[1]
password = sys.argv[2]
filename = sys.argv[3][:-5] + ".html"  # Trim .html or .HTML if needed

def get_html_file(host, user, password, filename):
    command = f'lftp -u {user},{password} {host} -e "cat {filename}; bye"'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode("latin1")  # Using latin1 to avoid decode errors

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
    # Remove <pre> blocks containing "Command not valid before LOGON"
    pattern = r'<pre>.*?HCPCFC015E Command not valid before LOGON: ID.*?</pre>'
    return re.sub(pattern, '', html, flags=re.DOTALL)

def write_summary_to_csv(summary, filename="test_summary.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Count"])
        for key, value in summary.items():
            writer.writerow([key, value])

# Main logic
html_content = get_html_file(host, user, password, filename)
summary = parse_html(html_content)
cleaned_html = remove_unwanted_pre_blocks(html_content)

# Save CSV for Jenkins artifacts
write_summary_to_csv(summary)

# Output
print("Test Summary from HTML:", summary)
print("\n--- HTML Content Start ---\n")
print(cleaned_html.strip())
print("\n--- HTML Content End ---\n")
