import os

names = ["Alice", "Bob", "Charlie"]
path = "/tmp/names.txt"

with open(path, "w") as f:
    for name in names:
        f.write(name + "\n")

print(f"✅ File created: {os.path.exists(path)}")
print(f"✅ Written to: {path}")
