import sys

def process_data(hatt_file, user_id, password, output_format):
    print(f"Selected HATT File: {hatt_file}")
    print(f"Target VM User ID: {user_id}")
    print(f"Target VM Password: {password}")
    print(f"Output Format: {output_format}")
    
    # Sample logic to demonstrate further actions
    print(f"Processing {hatt_file} for user {user_id} with {output_format} format...")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Error: Missing arguments.")
        sys.exit(1)

    hatt_file = sys.argv[1]
    user_id = sys.argv[2]
    password = sys.argv[3]
    output_format = sys.argv[4]

    process_data(hatt_file, user_id, password, output_format)
