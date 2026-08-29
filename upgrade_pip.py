import subprocess
import sys

# Upgrade pip
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
    capture_output=True, text=True, timeout=60
)
print('STDOUT:', result.stdout[-500:])
print('STDERR:', result.stderr[-500:])
print('Return code:', result.returncode)