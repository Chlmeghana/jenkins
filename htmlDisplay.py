import subprocess
import re
import sys
import codecs

# FTP details
host = "gdlfcft.endicott.ibm.com"
user = "meghana"
password = "B@NGAL0R"
filename = sys.argv[1]

def get_html_file(host, user, password, filename):
    command = f'lftp -u {user},{password} {host} -e "cat {filename}; bye"'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    # Try decoding: latin1 first, fallback to cp037
    try:
        html = output.decode("latin1")
        if "<html" not in html and "<HTML" not in html:
            raise UnicodeDecodeError("latin1", output, 0, 1, "Not HTML-like content")
        return html
    except UnicodeDecodeError:
        try:
            return codecs.decode(output, "cp037")
        except Exception as e:
            print(f"Decoding failed: {e}")
            return output.decode('utf-8', errors='replace')  # as a last resort

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
    # Remove all <pre> blocks that contain "Command not valid before LOGON"
    pattern = r'<pre>.*?HCPCFC015E Command not valid before LOGON: ID.*?</pre>'
    return re.sub(pattern, '', html, flags=re.DOTALL)

# Main logic
html_content = get_html_file(host, user, password, filename)
summary = parse_html(html_content)
cleaned_html = remove_unwanted_pre_blocks(html_content)

# Output
print("Test Summary from HTML:", summary)
print("\n--- HTML Content Start ---\n")
print(cleaned_html.strip())
print("\n--- HTML Content End ---\n")
