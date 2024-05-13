"""
    SERS TEAM
    update_path.py
"""

import os
import pathlib

script_directory = pathlib.Path(os.path.abspath(__file__)).parent
relative_path = pathlib.Path("src/run.py")
absolute_target_file_path = pathlib.Path(script_directory.parent, relative_path)

file = ""

with open(absolute_target_file_path, "r") as code:
    file += f"absolute_directory = r'{absolute_target_file_path.parent}'\n"
    code.readline()
    file += code.read()

with open(absolute_target_file_path, "w") as code:
    code.write(file)

print("Successfully loaded or something: your new path is:", absolute_target_file_path)

