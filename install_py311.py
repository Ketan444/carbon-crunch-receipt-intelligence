import subprocess
import os

exe = r'C:\Users\ketan_hvrftcf\Downloads\python-3.11.9-amd64.exe'
args = ['/quiet', 'PrependPath=1', f'TargetDir="C:\\Python311"']
result = subprocess.run([exe] + args, capture_output=True, text=True, timeout=300)
print('STDOUT:', result.stdout[-500:])
print('STDERR:', result.stderr[-500:])
print('Return code:', result.returncode)

# Verify
result2 = subprocess.run([r'C:\Python311\python.exe', '--version'], capture_output=True, text=True)
print('Python 3.11 version:', result2.stdout.strip())

result3 = subprocess.run([r'C:\Python311\python.exe', '-m', 'pip', '--version'], capture_output=True, text=True)
print('Pip version:', result3.stdout.strip())