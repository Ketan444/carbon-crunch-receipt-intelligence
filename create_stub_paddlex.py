import os
import sys

paddlex_dir = r'C:\Users\ketan_hvrftcf\AppData\Roaming\Python\Python314\site-packages\paddlex'
os.makedirs(paddlex_dir, exist_ok=True)

# Create __init__.py
with open(os.path.join(paddlex_dir, '__init__.py'), 'w') as f:
    f.write('# Minimal stub paddlex module\n')
    f.write('create_predictor = lambda: None\n')
    f.write('DependencyError = Exception\n')
    f.write('__all__ = ["create_predictor", "DependencyError"]\n')

# Create utils submodule
utils_dir = os.path.join(paddlex_dir, 'utils')
os.makedirs(utils_dir, exist_ok=True)

with open(os.path.join(utils_dir, '__init__.py'), 'w') as f:
    f.write('# Minimal stub paddlex.utils module\n')
    f.write('DependencyError = Exception\n')

# Add to path
if paddlex_dir not in sys.path:
    sys.path.insert(0, paddlex_dir)

print('Created stub paddlex module and utils submodule')