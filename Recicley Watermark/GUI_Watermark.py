import sys
import os
import io
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QPushButton, QMessageBox, QSlider
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from pdf2image import convert_from_bytes
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image

def get_base_path():
    """ Obtiene la ruta del directorio donde se ejecuta el script o el .exe """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class DragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setWindowTitle("Recicley Watermark")
        
        # Ruta dinámica para el ícono
        icon_path = os.path.join(get_base_path(), "rec.jpg")
        self.setWindowIcon(QIcon(icon_path))
        
        self.setMinimumSize(500, 500)
        self.setMaximumSize(500, 500)
        self.setStyleSheet(
            "font-size: 30px; background: #b6d7a8; color: white; font-family: sans-serif")

        # Contenedor principal
        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)

        # Título
        self.title = QLabel("Protector de archivos", self.mainWidget)
        self.title.setStyleSheet(
            "background: #f1c232; padding-left:50px; border-radius: 30%;")
        self.title.setGeometry(50, 20, 400, 70)

        # Label para PDF
        self.label_pdf = QLabel("Arrastra el archivo PDF", self.mainWidget)
        self.label_pdf.setGeometry(75, 100, 350, 100)
        self.label_pdf.setStyleSheet(
            "background: white; padding-left: 17px; color: #f1c232")

        self.pdf_path = ""
        self.watermark_path = ""

        # Label para Imagen de Marca de Agua
        self.label_watermark = QLabel(
            "Arrastra la imagen de marca de agua", self.mainWidget)
        self.label_watermark.setGeometry(75, 210, 350, 100)
        self.label_watermark.setStyleSheet(
            "background: white; padding-left: 17px; color: #3d85c6")

        # Slider para opacidad
        self.opacity_label = QLabel("Opacidad: 128", self.mainWidget)
        self.opacity_label.setGeometry(75, 320, 350, 30)
        self.opacity_label.setStyleSheet("color: #3d85c6")

        self.opacity_slider = QSlider(
            Qt.Orientation.Horizontal, self.mainWidget)
        self.opacity_slider.setGeometry(75, 360, 350, 30)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(128)  
        self.opacity_slider.valueChanged.connect(self.updateOpacity)

        # Botón
        self.button = QPushButton("Agregar Marca de Agua", self)
        self.button.setGeometry(150, 400, 190, 30)
        self.button.setStyleSheet(
            "background: #3d85c6; color: white; font-size:15px; border-radius: 10px")
        self.button.clicked.connect(self.processWatermark)

    def updateOpacity(self):
        self.opacity = self.opacity_slider.value()
        self.opacity_label.setText(f"Opacidad: {self.opacity}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toString().lower()
                if file_path.endswith('.pdf') or file_path.endswith(('.png', '.jpg', '.jpeg')):
                    event.acceptProposedAction()
                    break

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    self.pdf_path = file_path
                    self.label_pdf.setText(
                        f"Archivo PDF: {os.path.basename(self.pdf_path)}")
                elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.watermark_path = file_path
                    self.label_watermark.setText(
                        f"Marca de agua: {os.path.basename(self.watermark_path)}")

    def processWatermark(self):
        if not self.pdf_path:
            QMessageBox.warning(self, "Error", "Por favor, arrastra un archivo PDF primero.")
            return
        if not self.watermark_path:
            QMessageBox.warning(self, "Error", "Por favor, arrastra una imagen para la marca de agua primero.")
            return

        try:
            self.addWaterMarkToPDF(self.pdf_path, self.watermark_path)
            QMessageBox.information(self, "Éxito", "Marca de agua agregada exitosamente. Guardado en Descargas.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")

    def addWaterMarkToPDF(self, pdf_path, watermark_path):
        base_path = get_base_path()
        poppler_path = os.path.join(base_path, "poppler-0.68.0", "bin")
        
        # --- CAMBIO AQUÍ: Buscar la carpeta de descargas del usuario ---
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        output_path = os.path.join(
            downloads_folder, f"{os.path.basename(pdf_path).replace('.pdf', '')}_marca_de_agua.pdf")

        waterMark = Image.open(watermark_path)
        opacity = self.opacity_slider.value()

        pdf_writer = PdfWriter()
        pdf_reader = PdfReader(pdf_path)

        buffers_memoria = []

        for page_num in range(len(pdf_reader.pages)):
            pdf_writer_temp = PdfWriter()
            pdf_writer_temp.add_page(pdf_reader.pages[page_num])
            
            temp_pdf_io = io.BytesIO()
            pdf_writer_temp.write(temp_pdf_io)
            temp_pdf_bytes = temp_pdf_io.getvalue()

            page_image = convert_from_bytes(
                temp_pdf_bytes, poppler_path=poppler_path, dpi=72)[0]
            page_image = page_image.convert("RGBA")

            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.ANTIALIAS

            watermark_resized = waterMark.resize(
                page_image.size, resample_filter).convert("RGBA")
            watermark_resized.putalpha(opacity)

            page_with_watermark = Image.alpha_composite(
                page_image, watermark_resized)

            watermarked_pdf_io = io.BytesIO()
            page_with_watermark.convert("RGB").save(
                watermarked_pdf_io, format="PDF", quality=75)
            
            watermarked_pdf_io.seek(0)
            buffers_memoria.append(watermarked_pdf_io) 

            watermarked_page_pdf = PdfReader(watermarked_pdf_io)
            pdf_writer.add_page(watermarked_page_pdf.pages[0])

        with open(output_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)


def main():
    app = QApplication(sys.argv)
    window = DragDropWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()