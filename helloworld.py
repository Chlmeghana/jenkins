names = ["Alice", "Bob", "Charlie"]
with open("/tmp/names.txt", "w") as f:
    for name in names:
        f.write(name + "\n")
