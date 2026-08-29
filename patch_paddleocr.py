import os
import re

site_packages = r'C:\Users\ketan_hvrftcf\AppData\Roaming\Python\Python314\site-packages'
paddleocr_dir = os.path.join(site_packages, 'paddleocr')

# Read all paddleocr .py files and find paddlex imports
for root, dirs, files in os.walk(paddleocr_dir):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                # Check for paddlex imports
                if 'paddlex' in content:
                    # Remove paddlex imports
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        # Skip or replace paddlex imports
                        if re.match(r'^\s*from paddlex', line) or re.match(r'^\s*import paddlex', line):
                            # Replace with a comment
                            new_lines.append('# ' + line.strip() + '  # stubbed for env compatibility')
                        else:
                            new_lines.append(line)
                    content = '\n'.join(new_lines)
                    with open(filepath, 'w', encoding='utf-8') as fh:
                        fh.write(content)
                    print('Patched: ' + filepath)
            except Exception as e:
                print('Error patching ' + filepath + ': ' + str(e))

print('Done patching paddleocr modules')