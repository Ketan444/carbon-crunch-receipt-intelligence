import subprocess
import sys

python_path = r"C:\Users\ketan_hvrftcf\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe"

# Upgrade pip
result = subprocess.run(
    [python_path, "-m", "pip", "install", "--upgrade", "pip"],
    capture_output=True, text=True, timeout=60
)
print("=== Upgrade pip ===")
print("STDOUT:", result.stdout[-500:])
print("STDERR:", result.stderr[-500:])
print("Return code:", result.returncode)

# Install core dependencies
deps = [
    "opencv-python-headless>=4.5.0",
    "pillow>=9.0.0",
    "numpy>=1.24.0",
    "pyyaml>=6.0.0",
    "paddleocr",
    "paddlepaddle",
    "pydantic>=2.0.0",
    "pytest>=7.0.0",
]

for dep in deps:
    print(f"\n=== Installing: {dep} ===")
    result = subprocess.run(
        [python_path, "-m", "pip", "install", dep],
        capture_output=True, text=True, timeout=120
    )
    print("STDOUT:", result.stdout[-300:])
    print("STDERR:", result.stderr[-300:])
    print("Return code:", result.returncode)
    if result.returncode != 0:
        print("FAILED!")