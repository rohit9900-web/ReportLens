import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import sys
import os
import platform

# 1. Safety Fix: Prevent "DecompressionBomb" crash
Image.MAX_IMAGE_PIXELS = None

def run_ocr(pdf_path, output_txt):
    # Configure Tesseract Path
    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# (If it's Linux/Streamlit, we don't need a path because it finds it automatically!)

    print(f"Processing: {os.path.basename(pdf_path)}")
    
    try:
        # Use 300 DPI
        images = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return False

    full_text = []
    # REMOVED EMOJI HERE
    print(f"Extracted {len(images)} pages. Starting OCR...")

    for i, image in enumerate(images):
        page_num = i + 1
        print(f" > Reading Page {page_num}...", end="\r")
        
        # --- PRE-PROCESSING ---
        gray_image = ImageOps.grayscale(image)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(gray_image, config=custom_config)
        
        # --- FORMATTING ---
        separator = f"\n========================= PAGE {page_num} =========================\n"
        full_text.append(separator + text)

    # Save to file
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("".join(full_text))
        
    # REMOVED EMOJI HERE TOO
    print(f"\nStep 1 Complete! Text saved to: {output_txt}")
    return True

if __name__ == "__main__":
    # Check if a filename was passed from Streamlit
    if len(sys.argv) > 1:
        PDF_INPUT = sys.argv[1]
    else:
        # Default for testing
        PDF_INPUT = r"D:\ReportLens Project\data\DISCHARGESUMMARY-compressed.pdf"

    print(f"Starting OCR on: {PDF_INPUT}")
    
    # Run the function
    success = run_ocr(PDF_INPUT, 'final_tesseract_output.txt')
    
    if not success:
        sys.exit(1)