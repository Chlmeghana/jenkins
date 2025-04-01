names = ["Alice", "Bob", "Charlie"]
with open("/tmp/names.txt", "w") as f:
    for name in names:
        f.write(name + "\n")

# Optional: print for Jenkins console
for name in names:
    print(name)
