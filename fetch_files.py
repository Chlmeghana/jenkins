import subprocess
import re

def fetch_ftp_files():
    host = "gdlfcft.endicott.ibm.com"
    user = "meghana"
    password = "B@NGAL0R"

    # Add full path to lftp for Jenkins environment
    lftp_path = "/usr/local/bin/lftp"  # Example path for macOS; update if different

    try:
        command = f"{lftp_path} -u {user},{password} {host} -e 'ls *.HATT; bye'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        file_list = re.findall(r'\b[A-Z0-9]+\.HATT\b', result.stdout)
        
        if file_list:
            print("Files found:")
            for file in file_list:
                print(file)
        else:
            print("No .HATT files found")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_ftp_files()
