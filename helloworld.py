names = ["Alice", "Bob", "Charlie"]
for name in names:
    print(name)

with open("/tmp/names.txt", "w") as f:
    for name in names:
        f.write(name + "\n")
