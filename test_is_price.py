import sys
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')
from receipt_ai.extraction import _is_price

test_texts = ['0.41', '1b', '0.20', 'BANANAS', '5.11', 'ST# 5748', '# ITEMS SOLD 2', 'OPEN 24']
for t in test_texts:
    result = _is_price(t)
    print(f'_is_price("{t}") = {result}')