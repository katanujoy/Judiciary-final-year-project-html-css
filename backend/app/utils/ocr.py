import pytesseract
from PIL import Image
import pdf2image
import os

def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image file using Tesseract OCR."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        # Configure tesseract: OEM 3 = Default LSTM OCR, PSM 6 = Assume a single uniform block of text
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(Image.open(image_path), config=custom_config)
        return text.strip()
    except Exception as e:
        raise Exception(f"OCR failed for image: {str(e)}")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF by converting each page to an image first."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        images = pdf2image.convert_from_path(pdf_path, dpi=300)
        full_text = ""
        for i, image in enumerate(images):
            # Optional: configure Tesseract for PDF images as well
            text = pytesseract.image_to_string(image)
            full_text += f"--- Page {i+1} ---\n{text}\n\n"
        return full_text.strip()
    except Exception as e:
        raise Exception(f"PDF OCR failed: {str(e)}")


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text from file based on MIME type."""
    if file_type == 'application/pdf':
        return extract_text_from_pdf(file_path)
    elif file_type.startswith('image/'):
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type for OCR: {file_type}")


def is_ocr_supported(file_type: str) -> bool:
    """Check if the file type is supported for OCR."""
    supported_types = {
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/tiff'
    }
    return file_type.lower() in supported_types
