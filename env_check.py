import subprocess
import sys

results = []

# python --version
try:
    r = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
    results.append(f"python --version: {r.stdout.strip()}")
except Exception as e:
    results.append(f"python --version: ERROR {e}")

# where python
try:
    r = subprocess.run(['where', 'python'], capture_output=True, text=True)
    results.append(f"where python: {r.stdout.strip()[:200]}")
except Exception as e:
    results.append(f"where python: ERROR {e}")

# pip --version
try:
    r = subprocess.run([sys.executable, '-m', 'pip', '--version'], capture_output=True, text=True)
    results.append(f"pip --version: {r.stdout.strip()}")
except Exception as e:
    results.append(f"pip --version: ERROR {e}")

# uv --version
try:
    r = subprocess.run(['uv', '--version'], capture_output=True, text=True)
    results.append(f"uv --version: {r.stdout.strip()}")
except Exception as e:
    results.append(f"uv --version: ERROR {e}")

# platform info
try:
    r = subprocess.run([sys.executable, '-c', 'import platform; print(platform.architecture(), platform.machine())'], capture_output=True, text=True)
    results.append(f"platform: {r.stdout.strip()[:200]}")
except Exception as e:
    results.append(f"platform: ERROR {e}")

# Print results
for line in results:
    print(line)