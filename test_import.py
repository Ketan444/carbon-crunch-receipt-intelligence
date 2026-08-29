import os
src_dir = r"C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src"

# Check if __init__.py exists
init_path = os.path.join(src_dir, "__init__.py")
if os.path.exists(init_path):
    # Remove it to test namespace package
    os.remove(init_path)
    print("Removed existing __init__.py")
else:
    print("No __init__.py found")

# Now test - use namespace package approach (no __init__.py needed)
import sys
# Clear any cached modules
for mod in list(sys.modules.keys()):
    if "receipt_ai" in mod:
        del sys.modules[mod]

sys.path.insert(0, src_dir)

# Try importing - this should work as a namespace package
try:
    import receipt_ai
    print("Module file:", receipt_ai.__file__)
    from receipt_ai.config import PROJECT_ROOT
    print("config OK:", PROJECT_ROOT)
except Exception as e:
    print(f"Error: {e}")
    # Try the old way with __init__.py
    print("\nTrying with __init__.py...")
    
    # Recreate minimal __init__.py
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("# Minimal package - no submodule imports at top level\n")
        f.write("__version__ = '1.0.0'\n")
    
    import receipt_ai
    print("Module file:", receipt_ai.__file__)
    from receipt_ai.config import PROJECT_ROOT
    print("config OK:", PROJECT_ROOT)