import sys

if len(sys.argv) != 2 or not sys.argv[1].strip():
    print("Error: No value received from Jenkins.")
    sys.exit(1)

selected_value = sys.argv[1]
print(f"Selected Value: {selected_value}")

