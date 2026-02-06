import logging

import pytesseract
from PIL import Image, ImageFilter, ImageOps

from src.processors.base import BaseProcessor

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp")


class OCRProcessor(BaseProcessor):

    def __init__(self, languages: str = "fra+eng"):
        self.languages = languages

    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(SUPPORTED_EXTENSIONS)

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        if image.mode != "L":
            image = image.convert("L")
        image = ImageOps.autocontrast(image)
        image = image.filter(ImageFilter.SHARPEN)
        return image

    def extract_text(self, file_path: str) -> str:
        try:
            image = Image.open(file_path)
            processed = self._preprocess_image(image)
            text = pytesseract.image_to_string(processed, lang=self.languages)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path}: {e}")
            raise

    def extract_metadata(self, file_path: str) -> dict:
        try:
            image = Image.open(file_path)
            return {
                "source": "ocr",
                "ocrEngine": "tesseract",
                "languages": self.languages,
                "imageFormat": image.format,
                "imageSize": {"width": image.width, "height": image.height},
                "imageMode": image.mode,
            }
        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            return {
                "source": "ocr",
                "ocrEngine": "tesseract",
                "languages": self.languages,
            }
