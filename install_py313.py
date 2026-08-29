import subprocess
import os

exe = r'C:\Users\ketan_hvrftcf\Downloads\python-3.13.7-amd64.exe'
args = ['/quiet', 'IncludePy=true', 'PrependPath=1', f'TargetDir="C:\\Python313"']
result = subprocess.run([exe] + args, capture_output=True, text=True, timeout=300)
print('STDOUT:', result.stdout[-1000:])
print('STDERR:', result.stderr[-1000:])
print('Return code:', result.returncode)

# Verify
result2 = subprocess.run(['python313', '--version'], capture_output=True, text=True)
print('Python 3.13 version:', result2.stdout.strip())

result3 = subprocess.run(['python313', '-m', 'pip', '--version'], capture_output=True, text=True)
print('Pip version:', result3.stdout.strip())