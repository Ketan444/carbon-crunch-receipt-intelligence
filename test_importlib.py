import sys
import os

# Add src to path
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')

# Import modules directly by their file paths, bypassing the package name
import importlib.util

# Config
config_path = os.path.join(sys.path[0], 'receipt_ai', 'config.py')
config_spec = importlib.util.spec_from_file_location('receipt_ai_config', config_path)
config_mod = importlib.util.module_from_spec(config_spec)
config_spec.loader.exec_module(config_mod)
print('config OK:', hasattr(config_mod, 'PROJECT_ROOT'))

# Schemas
schemas_path = os.path.join(sys.path[0], 'receipt_ai', 'schemas.py')
schemas_spec = importlib.util.spec_from_file_location('receipt_ai_schemas', schemas_path)
schemas_mod = importlib.util.module_from_spec(schemas_spec)
schemas_spec.loader.exec_module(schemas_mod)
print('schemas OK')

# Quality
quality_path = os.path.join(sys.path[0], 'receipt_ai', 'quality.py')
quality_spec = importlib.util.spec_from_file_location('receipt_ai_quality', quality_path)
quality_mod = importlib.util.module_from_spec(quality_spec)
quality_spec.loader.exec_module(quality_mod)
print('quality OK')

# Preprocessing
preprocessing_path = os.path.join(sys.path[0], 'receipt_ai', 'preprocessing.py')
preprocessing_spec = importlib.util.spec_from_file_location('receipt_ai_preprocessing', preprocessing_path)
preprocessing_mod = importlib.util.module_from_spec(preprocessing_spec)
preprocessing_spec.loader.exec_module(preprocessing_mod)
print('preprocessing OK')

# OCR
ocr_path = os.path.join(sys.path[0], 'receipt_ai', 'ocr.py')
ocr_spec = importlib.util.spec_from_file_location('receipt_ai_ocr', ocr_path)
ocr_mod = importlib.util.module_from_spec(ocr_spec)
ocr_spec.loader.exec_module(ocr_mod)
print('ocr OK')

# OCR normalization
ocr_norm_path = os.path.join(sys.path[0], 'receipt_ai', 'ocr_normalization.py')
ocr_norm_spec = importlib.util.spec_from_file_location('receipt_ai_ocr_norm', ocr_norm_path)
ocr_norm_mod = importlib.util.module_from_spec(ocr_norm_spec)
ocr_norm_spec.loader.exec_module(ocr_norm_mod)
print('ocr_normalization OK')

# Extraction
extraction_path = os.path.join(sys.path[0], 'receipt_ai', 'extraction.py')
extraction_spec = importlib.util.spec_from_file_location('receipt_ai_extraction', extraction_path)
extraction_mod = importlib.util.module_from_spec(extraction_spec)
extraction_spec.loader.exec_module(extraction_mod)
print('extraction OK')

# Total extraction
total_path = os.path.join(sys.path[0], 'receipt_ai', 'total_extraction.py')
total_spec = importlib.util.spec_from_file_location('receipt_ai_total', total_path)
total_mod = importlib.util.module_from_spec(total_spec)
total_spec.loader.exec_module(total_mod)
print('total_extraction OK')

# Date extraction
date_path = os.path.join(sys.path[0], 'receipt_ai', 'date_extraction.py')
date_spec = importlib.util.spec_from_file_location('receipt_ai_date', date_path)
date_mod = importlib.util.module_from_spec(date_spec)
date_spec.loader.exec_module(date_mod)
print('date_extraction OK')

# Validation
validation_path = os.path.join(sys.path[0], 'receipt_ai', 'validation.py')
validation_spec = importlib.util.spec_from_file_location('receipt_ai_validation', validation_path)
validation_mod = importlib.util.module_from_spec(validation_spec)
validation_spec.loader.exec_module(validation_mod)
print('validation OK')

# Confidence
confidence_path = os.path.join(sys.path[0], 'receipt_ai', 'confidence.py')
confidence_spec = importlib.util.spec_from_file_location('receipt_ai_confidence', confidence_path)
confidence_mod = importlib.util.module_from_spec(confidence_spec)
confidence_spec.loader.exec_module(confidence_mod)
print('confidence OK')

# Conflict resolution
conflict_path = os.path.join(sys.path[0], 'receipt_ai', 'conflict_resolution.py')
conflict_spec = importlib.util.spec_from_file_location('receipt_ai_conflict', conflict_path)
conflict_mod = importlib.util.module_from_spec(conflict_spec)
conflict_spec.loader.exec_module(conflict_mod)
print('conflict_resolution OK')

# Summary
summary_path = os.path.join(sys.path[0], 'receipt_ai', 'summary.py')
summary_spec = importlib.util.spec_from_file_location('receipt_ai_summary', summary_path)
summary_mod = importlib.util.module_from_spec(summary_spec)
summary_spec.loader.exec_module(summary_mod)
print('summary OK')

print('\nALL MODULES LOADED SUCCESSFULLY VIA importlib')