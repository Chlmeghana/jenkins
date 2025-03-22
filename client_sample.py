import sys

if len(sys.argv) != 2:
    print("Usage: python3 your_script.py <value>")
    sys.exit(1)

selected_value = sys.argv[1]
print(f"Selected Value: {selected_value}")
