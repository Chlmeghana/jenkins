import subprocess
import re

def fetch_ftp_files():
    host = "gdlfcft.endicott.ibm.com"
    user = "meghana"
    password = "B@NGAL0R"  # For security, consider fetching this from environment variables.

    # Run the lftp command to connect and list files
    try:
        command = f"lftp -u {user},{password} {host} -e 'ls *.HATT; bye'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        # Extract file names using refined regex to capture only valid filenames
        file_list = re.findall(r'\b[A-Z0-9]+\.HATT\b', result.stdout)

        # Display the file list
        print("Files found:")
        for file in file_list:
            print(file)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_ftp_files()
