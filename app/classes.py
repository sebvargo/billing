# PDF Reader class import
from PIL import Image
from tesserocr import PyTessBaseAPI
import fitz  # PyMuPDF
import io
import os


OPEN_AI_EMBEDDINGS_MODEL = os.environ.get("OPEN_AI_EMBEDDINGS_MODEL")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME")
TESSERACT_PATH = os.environ.get("TESSERACT_PATH")

class PDFClient:
    def __init__(self, pdf_path, tessdata_path=TESSERACT_PATH):
        self.pdf_path = pdf_path
        self.tessdata_path = tessdata_path

    def get_pdf_pages(self):
        """Open a PDF and return a list of page objects."""
        pdf = fitz.open(self.pdf_path)
        pages = [pdf.load_page(page_num) for page_num in range(len(pdf))]
        return pages

    def pages_to_images(self, pages, zoom_x=3.0, zoom_y=3.0):
        """Convert a list of PDF page objects into images."""
        images = []
        for page in pages:
            mat = fitz.Matrix(zoom_x, zoom_y)  # Define a matrix for higher resolution.
            pix = page.get_pixmap(matrix=mat)  # Render page to an image.
            img_bytes = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_bytes))  # Open the image with PIL.
            images.append(image)
        return images

    def images_to_texts_list(self, images):
        """Convert a list of images into a block of text using OCR."""
        texts = []
        with PyTessBaseAPI(path=self.tessdata_path) as api:
            for image in images:
                api.SetImage(image)
                texts.append(api.GetUTF8Text())
        return texts

    def extract_text(self):
        """Extract text from the entire PDF."""
        pages = self.get_pdf_pages()
        images = self.pages_to_images(pages)
        texts = self.images_to_texts_list(images)
        self.texts = texts
        return pages, images, texts
        