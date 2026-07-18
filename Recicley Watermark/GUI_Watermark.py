import sys
import os
import io
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QPushButton, QMessageBox,
    QSlider, QFileDialog, QProgressDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from pdf2image import convert_from_bytes
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image

RENDER_DPI = 200
PDF_SAVE_QUALITY = 95

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')


def get_base_path():
    """ Obtiene la ruta donde están los recursos empaquetados (rec.jpg, poppler).
    En el .exe, PyInstaller extrae/coloca los datos en sys._MEIPASS. """
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


class DragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setWindowTitle("Recicley Watermark")

        # Ruta dinámica para el ícono
        icon_path = os.path.join(get_base_path(), "rec.jpg")
        self.setWindowIcon(QIcon(icon_path))

        self.setMinimumSize(500, 520)
        self.setMaximumSize(500, 520)
        self.setStyleSheet(
            "font-size: 18px; background: #b6d7a8; color: white; font-family: sans-serif")

        # Contenedor principal
        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)

        # Título
        self.title = QLabel("Protector de archivos", self.mainWidget)
        self.title.setStyleSheet(
            "font-size: 30px; background: #f1c232; padding-left:50px; border-radius: 30%;")
        self.title.setGeometry(50, 15, 400, 55)

        self.pdf_paths = []
        self.watermark_path = ""
        self.output_dir = ""

        # Label para PDF(s)
        self.label_pdf = QLabel("Arrastra PDF(s) o una carpeta aquí", self.mainWidget)
        self.label_pdf.setGeometry(75, 78, 350, 55)
        self.label_pdf.setWordWrap(True)
        self.label_pdf.setStyleSheet(
            "font-size:14px; background: white; padding-left: 17px; color: #f1c232")

        # Botones para elegir archivos / carpeta / limpiar
        self.button_select_files = QPushButton("Archivos", self.mainWidget)
        self.button_select_files.setGeometry(75, 141, 110, 28)
        self.button_select_files.setStyleSheet(
            "font-size:13px; background: #f1c232; color: white; border-radius: 8px")
        self.button_select_files.clicked.connect(self.selectFilesDialog)

        self.button_select_folder = QPushButton("Carpeta", self.mainWidget)
        self.button_select_folder.setGeometry(195, 141, 110, 28)
        self.button_select_folder.setStyleSheet(
            "font-size:13px; background: #f1c232; color: white; border-radius: 8px")
        self.button_select_folder.clicked.connect(self.selectFolderDialog)

        self.button_clear_files = QPushButton("Limpiar", self.mainWidget)
        self.button_clear_files.setGeometry(315, 141, 110, 28)
        self.button_clear_files.setStyleSheet(
            "font-size:13px; background: #f1c232; color: white; border-radius: 8px")
        self.button_clear_files.clicked.connect(self.clearFiles)

        # Label para Imagen de Marca de Agua
        self.label_watermark = QLabel(
            "Arrastra la imagen de marca de agua", self.mainWidget)
        self.label_watermark.setGeometry(75, 177, 350, 50)
        self.label_watermark.setWordWrap(True)
        self.label_watermark.setStyleSheet(
            "font-size:14px; background: white; padding-left: 17px; color: #3d85c6")

        self.button_select_watermark = QPushButton("Elegir imagen", self.mainWidget)
        self.button_select_watermark.setGeometry(75, 233, 350, 26)
        self.button_select_watermark.setStyleSheet(
            "font-size:13px; background: #3d85c6; color: white; border-radius: 8px")
        self.button_select_watermark.clicked.connect(self.selectWatermarkDialog)

        # Label + botón para carpeta de destino
        self.label_output = QLabel(
            "Destino: predeterminado (Descargas)", self.mainWidget)
        self.label_output.setGeometry(75, 267, 350, 50)
        self.label_output.setWordWrap(True)
        self.label_output.setStyleSheet(
            "font-size:14px; background: white; padding-left: 17px; color: #6aa84f")

        self.button_select_output = QPushButton("Elegir destino", self.mainWidget)
        self.button_select_output.setGeometry(75, 323, 350, 26)
        self.button_select_output.setStyleSheet(
            "font-size:13px; background: #6aa84f; color: white; border-radius: 8px")
        self.button_select_output.clicked.connect(self.selectOutputDialog)

        # Slider para opacidad
        self.opacity_label = QLabel("Opacidad: 128", self.mainWidget)
        self.opacity_label.setGeometry(75, 357, 350, 24)
        self.opacity_label.setStyleSheet("font-size:16px; color: #3d85c6")

        self.opacity_slider = QSlider(
            Qt.Orientation.Horizontal, self.mainWidget)
        self.opacity_slider.setGeometry(75, 385, 350, 26)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(128)
        self.opacity_slider.valueChanged.connect(self.updateOpacity)

        # Botón
        self.button = QPushButton("Agregar Marca de Agua", self.mainWidget)
        self.button.setGeometry(150, 419, 190, 34)
        self.button.setStyleSheet(
            "background: #3d85c6; color: white; font-size:15px; border-radius: 10px")
        self.button.clicked.connect(self.processWatermark)

    def updateOpacity(self):
        self.opacity = self.opacity_slider.value()
        self.opacity_label.setText(f"Opacidad: {self.opacity}")

    # --- Gestión de la lista de PDFs ---

    def add_pdf(self, path):
        if path not in self.pdf_paths:
            self.pdf_paths.append(path)

    def add_pdfs_from_folder(self, folder):
        found = []
        for root, _dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith('.pdf'):
                    found.append(os.path.join(root, f))
        for f in sorted(found):
            self.add_pdf(f)

    def update_pdf_label(self):
        n = len(self.pdf_paths)
        if n == 0:
            self.label_pdf.setText("Arrastra PDF(s) o una carpeta aquí")
            self.label_pdf.setToolTip("")
        elif n == 1:
            self.label_pdf.setText(
                f"Archivo PDF: {os.path.basename(self.pdf_paths[0])}")
            self.label_pdf.setToolTip(self.pdf_paths[0])
        else:
            self.label_pdf.setText(f"{n} archivos PDF seleccionados")
            self.label_pdf.setToolTip(
                "\n".join(os.path.basename(p) for p in self.pdf_paths))

    def clearFiles(self):
        self.pdf_paths = []
        self.update_pdf_label()

    # --- Diálogos de selección ---

    def selectFilesDialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivo(s) PDF", "", "Archivos PDF (*.pdf)")
        for f in files:
            self.add_pdf(f)
        self.update_pdf_label()

    def selectFolderDialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder:
            self.add_pdfs_from_folder(folder)
            self.update_pdf_label()

    def selectWatermarkDialog(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de marca de agua", "",
            "Imágenes (*.png *.jpg *.jpeg)")
        if file:
            self.watermark_path = file
            self.label_watermark.setText(
                f"Marca de agua: {os.path.basename(file)}")

    def selectOutputDialog(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino")
        if folder:
            self.output_dir = folder
            self.label_output.setText(f"Destino: {folder}")
            self.label_output.setToolTip(folder)

    # --- Drag & Drop ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if (os.path.isdir(file_path)
                        or file_path.lower().endswith('.pdf')
                        or file_path.lower().endswith(IMAGE_EXTENSIONS)):
                    event.acceptProposedAction()
                    break

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isdir(file_path):
                self.add_pdfs_from_folder(file_path)
            elif file_path.lower().endswith('.pdf'):
                self.add_pdf(file_path)
            elif file_path.lower().endswith(IMAGE_EXTENSIONS):
                self.watermark_path = file_path
                self.label_watermark.setText(
                    f"Marca de agua: {os.path.basename(self.watermark_path)}")
        self.update_pdf_label()

    # --- Procesamiento ---

    def processWatermark(self):
        if not self.pdf_paths:
            QMessageBox.warning(
                self, "Error",
                "Por favor, arrastra o selecciona al menos un archivo PDF.")
            return
        if not self.watermark_path:
            QMessageBox.warning(
                self, "Error",
                "Por favor, arrastra o selecciona una imagen para la marca de agua.")
            return

        base_path = get_base_path()
        poppler_path = os.path.join(base_path, "poppler-0.68.0", "bin")
        base_output = self.output_dir or os.path.join(
            os.path.expanduser("~"), "Downloads")
        opacity = self.opacity_slider.value()

        if len(self.pdf_paths) == 1:
            output_dir = base_output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(
                base_output, f"Recicley_Watermark_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)

        total = len(self.pdf_paths)
        progress = QProgressDialog(
            "Procesando archivos...", "Cancelar", 0, total, self)
        progress.setWindowTitle("Recicley Watermark")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        used_names = set()
        errors = []
        processed = 0

        for i, pdf_path in enumerate(self.pdf_paths):
            if progress.wasCanceled():
                break
            filename = os.path.basename(pdf_path)
            progress.setLabelText(f"Procesando: {filename} ({i + 1}/{total})")
            progress.setValue(i)
            QApplication.processEvents()

            out_name = self.unique_output_name(
                used_names, f"{os.path.splitext(filename)[0]}_marca_de_agua.pdf")
            output_path = os.path.join(output_dir, out_name)

            try:
                self.addWaterMarkToPDF(
                    pdf_path, self.watermark_path, opacity, poppler_path, output_path)
                processed += 1
            except Exception as e:
                errors.append(f"{filename}: {e}")

        progress.setValue(total)

        if processed > 0:
            try:
                os.startfile(output_dir)
            except Exception:
                pass

        if errors:
            msg = (f"Se procesaron {processed} de {total} archivo(s).\n\n"
                   f"Errores:\n" + "\n".join(errors))
            QMessageBox.warning(self, "Proceso finalizado con errores", msg)
        elif processed > 0:
            QMessageBox.information(
                self, "Éxito",
                f"Se agregó la marca de agua a {processed} archivo(s).\n"
                f"Guardado en:\n{output_dir}")

    @staticmethod
    def unique_output_name(used_names, filename):
        base, ext = os.path.splitext(filename)
        candidate = filename
        i = 1
        while candidate in used_names:
            candidate = f"{base} ({i}){ext}"
            i += 1
        used_names.add(candidate)
        return candidate

    def addWaterMarkToPDF(self, pdf_path, watermark_path, opacity, poppler_path, output_path):
        waterMark = Image.open(watermark_path)

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
                temp_pdf_bytes, poppler_path=poppler_path, dpi=RENDER_DPI)[0]
            page_image = page_image.convert("RGBA")

            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.ANTIALIAS

            watermark_resized = waterMark.resize(
                page_image.size, resample_filter).convert("RGBA")
            original_alpha = watermark_resized.getchannel("A")
            scaled_alpha = original_alpha.point(
                lambda a, opacity=opacity: a * opacity // 255)
            watermark_resized.putalpha(scaled_alpha)

            page_with_watermark = Image.alpha_composite(
                page_image, watermark_resized)

            watermarked_pdf_io = io.BytesIO()
            page_with_watermark.convert("RGB").save(
                watermarked_pdf_io, format="PDF", quality=PDF_SAVE_QUALITY,
                resolution=RENDER_DPI)

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
