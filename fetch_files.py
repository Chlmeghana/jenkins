# fetch_files.py
import subprocess
import re
import sys

def fetch_ftp_files():
    host = "gdlfcft.endicott.ibm.com"
    user = "meghana"
    password = "B@NGAL0R"
    lftp_path = "/usr/local/bin/lftp"

    try:
        command = f"{lftp_path} -u {user},{password} {host} -e 'ls *.HATT; bye'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        file_list = re.findall(r'\b[A-Z0-9]+\.HATT\b', result.stdout)
        print(",".join(file_list))  # Return list in comma-separated format
    except Exception as e:
        print("ERROR")

if __name__ == "__main__":
    fetch_ftp_files()
