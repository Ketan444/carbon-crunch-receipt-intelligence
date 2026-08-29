import os

path = r"C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src\_init__.py"
with open(path, "w", encoding='utf-8') as f:
    f.write("# Carbon Crunch Receipt Intelligence package\n")
    f.write("\n")
    f.write("__version__ = \"1.0.0\"\n")

print("Created minimal _init__.py")

# Also create the double-underscore version
path2 = r"C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src\_\_init__.py"
with open(path2, "w", encoding='utf-8') as f:
    f.write("# Carbon Crunch Receipt Intelligence package\n")
    f.write("\n")
    f.write("__version__ = \"1.0.0\"\n")

print("Created minimal __init__.py")