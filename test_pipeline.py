import sys
sys.path.insert(0, r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\src')
from receipt_ai.pipeline import CarbonCrunchPipeline
from pathlib import Path

# Initialize pipeline with fallback OCR (since PaddleOCR pipeline has dependency issues)
pipeline = CarbonCrunchPipeline(ocr_engine='fallback')

# Process a small batch
sample_dir = Path(r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\data\raw')
print('Processing sample directory:', sample_dir)

# Only process 3 images for testing
results = pipeline.process_batch(sample_dir, output_dir=Path(r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\outputs\test'))

print('Processing summary:')
print('  Total images:', results['total_images'])
print('  Successfully processed:', results['successfully_processed'])
print('  Failed:', results['failed'])
print('  Partially processed:', results['partially_processed'])
print('  Financial summary total:', results['financial_summary_total'])
print('  Number of transactions:', results['number_of_transactions'])
print('  Evaluation report:', results['evaluation_report_path'])
print('  Expense summary:', results['expense_summary_path'])