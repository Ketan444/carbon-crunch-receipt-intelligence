import os
import paddleocr

# Initialize PaddleOCR
ocr = paddleocr.PaddleOCR(lang='en', use_angle_cls=False)
print('PaddleOCR initialized successfully')

# Test with a sample image from the dataset
sample_dir = r'C:\Users\ketan_hvrftcf\OneDrive\Desktop\PROJECTS\Carbon-Crunch-Receipt-Intelligence\data\raw'
images = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))][:1]
print('Sample images found:', len(images))
if images:
    result = ocr.ocr(os.path.join(sample_dir, images[0]), cls=False)
    print('OCR result type:', type(result))
    if result and result[0]:
        print('First OCR result:', result[0][0])
    else:
        print('No OCR result')
else:
    print('No images found')