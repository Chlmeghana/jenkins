import subprocess
import re
import os

def fetch_ftp_files():
    host = "gdlfcft.endicott.ibm.com"
    user = "meghana"
    password = os.getenv("FTP_PASSWORD", "B@NGAL0R")

    try:
        # Get file listing
        command = f"lftp -u {user},{password} {host} -e 'ls; bye'"
        result = subprocess.run(command, shell=True, capture_output=True)

        # Get PXBUCKET.H$$$ content
        command2 = f"lftp -u {user},{password} {host} -e 'cat SR2BUCK4.H$$$ ; bye'"
        result2 = subprocess.run(command2, shell=True, capture_output=True)

        # Decode using cp500 (EBCDIC)
        ls_output = result.stdout.decode('latin1', errors='replace')
        try:
            cat_output = result2.stdout.decode('cp500', errors='replace')
        except UnicodeDecodeError:
            cat_output = result2.stdout.decode('latin1', errors='replace')  # fallback

        if result.returncode != 0:
            print("FTP connection failed:")
            print(result.stderr.decode('latin1', errors='replace'))
            return

        # Extract file names
        file_list = re.findall(r'\b[A-Z0-9]+(?:\$\$\$)?\.(?:HATT|HTML|F1|G1)\b', ls_output)

        # Display file list
       # print("Files found:")
        #for file in sorted(set(file_list)):
         #   print(file)

        # Display PXBUCKET.H$$$ content
        print("\n--- Content of PXBUCKET.H$$$ ---")
        print(cat_output.strip())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_ftp_files()
