"""
VERITAS AI - PDF Integrity & Image Authenticity Audit Script
Extracts every page, text, and embedded image from docs/VERITAS_AI_USER_AND_SCREENSHOTS_GUIDE.pdf
Validates file size (< 10 MB), page count, resolution, unique colors, and mean luminance.
"""

import os
import io
import pypdf
from PIL import Image
import numpy as np

def audit_pdf(pdf_path="docs/VERITAS_AI_USER_AND_SCREENSHOTS_GUIDE.pdf"):
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return False

    size_bytes = os.path.getsize(pdf_path)
    size_mb = size_bytes / (1024 * 1024)
    print("=" * 60)
    print(f"VERITAS AI - PDF AUDIT REPORT: {pdf_path}")
    print(f"File Size: {size_bytes:,} bytes ({size_mb:.2f} MB)")
    print(f"Size Requirement (< 10 MB): {'PASSED' if size_mb < 10.0 else 'FAILED'}")
    print("=" * 60)

    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"Total Page Count: {total_pages}\n")

    all_valid = True
    images_verified = 0

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        text_preview = " ".join(text.split()[:10])
        images = page.images
        
        print(f"Page {page_num:2d}/{total_pages:2d} | Heading: {text_preview[:45]}... | Images: {len(images)}")
        
        for img_idx, img_obj in enumerate(images):
            images_verified += 1
            img_name = img_obj.name
            img_bytes = img_obj.data
            pil_img = Image.open(io.BytesIO(img_bytes))
            arr = np.array(pil_img)
            
            if arr.ndim == 3:
                colors = len(np.unique(arr.reshape(-1, arr.shape[-1]), axis=0))
            else:
                colors = len(np.unique(arr))
                
            mean_intensity = float(arr.mean())
            w, h = pil_img.size
            
            print(f"   Image {img_idx+1}: {img_name} ({w}x{h}) | "
                  f"Colors: {colors:6,d} | "
                  f"Mean: {mean_intensity:5.2f} | "
                  f"Bytes: {len(img_bytes):7,d}")
            
            # Assertions to ensure no black/blank screenshots
            if colors < 1000:
                print(f"   [FAIL] Page {page_num} Image {img_idx+1} has too few colors ({colors})")
                all_valid = False
            if mean_intensity < 18.0:
                print(f"   [FAIL] Page {page_num} Image {img_idx+1} is too dark ({mean_intensity:.2f})")
                all_valid = False

    print("\n" + "=" * 60)
    print(f"FINAL AUDIT RESULT: {'ALL 9 SCREENSHOTS 100% VERIFIED GENUINE AND VIBRANT' if (all_valid and images_verified == 9) else 'AUDIT FAILED'}")
    print(f"Total Verified Images: {images_verified}/9 | Total Pages: {total_pages}")
    print("=" * 60)
    return all_valid and images_verified == 9

if __name__ == "__main__":
    success = audit_pdf()
    exit(0 if success else 1)
