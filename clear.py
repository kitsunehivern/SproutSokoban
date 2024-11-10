import os

if os.path.exists("settings.json"):
    os.remove("settings.json")

os.chdir("Mazes")

for file in os.listdir():
    if file.startswith("output-") and file.endswith(".txt"):
        os.remove(file)

    if file.startswith("input-") and file.endswith(".txt"):
        if int(file[6:8]) > 10:
            os.remove(file)
