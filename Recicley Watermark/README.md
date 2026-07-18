# Recicley Watermark

Aplicación de escritorio para Windows que agrega una marca de agua (imagen PNG/JPG con transparencia) a uno o varios archivos PDF, en un solo paso y de forma idéntica en todos ellos.

## Características

- Arrastra y suelta uno o varios PDFs, o una carpeta completa (se buscan los PDF recursivamente en subcarpetas).
- Botones para elegir archivos o carpeta mediante el explorador de Windows, sin necesidad de arrastrar.
- Una sola imagen de marca de agua se aplica a todos los PDFs seleccionados.
- Control deslizante de opacidad (0–255).
- Carpeta de destino configurable (por defecto: `Descargas`).
- Barra de progreso con opción de cancelar durante el procesamiento por lotes.
- Reporte de errores por archivo sin detener el resto del lote.
- No requiere instalación ni Python: se distribuye como ejecutable portable de Windows.

## Requisitos

**Para usar el `.exe` (recomendado):** ninguno. Solo Windows 10/11 de 64 bits.

**Para ejecutar desde el código fuente:**
- Python 3.13
- Paquetes: `PyQt6`, `pdf2image`, `PyPDF2`, `Pillow`
- Poppler para Windows (incluido en la carpeta `poppler-0.68.0/`, usado por `pdf2image` para renderizar páginas del PDF)

## Instalación / distribución

1. Descomprime `GUI_Watermark_Windows.zip` en cualquier carpeta.
2. Entra a la carpeta resultante `GUI_Watermark/`.
3. Ejecuta `GUI_Watermark.exe`.

> Importante: el `.exe` necesita la carpeta `_internal` a su lado (contiene PyQt6, Poppler, el ícono y demás dependencias). No muevas ni copies el `.exe` por separado; comparte siempre la carpeta completa (o el `.zip`).

## Guía de uso

1. **Cargar el/los PDF(s).** Arrastra uno o varios archivos `.pdf` a la ventana, o arrastra una carpeta completa (se incluyen automáticamente todos los PDF de esa carpeta y sus subcarpetas). También puedes usar los botones:
   - **Archivos** — abre un selector para elegir uno o varios PDF.
   - **Carpeta** — abre un selector de carpeta y agrega todos los PDF que contenga.
   - **Limpiar** — vacía la lista de PDFs cargados.
2. **Cargar la marca de agua.** Arrastra una imagen `.png`, `.jpg` o `.jpeg` (idealmente PNG con canal alfa/transparencia) o usa el botón **Elegir imagen**. Esta misma imagen se aplicará a todos los PDF del paso anterior.
3. **Elegir destino (opcional).** Por defecto los resultados se guardan en la carpeta `Descargas` del usuario. Usa **Elegir destino** para guardarlos en otra carpeta.
4. **Ajustar opacidad.** Desliza el control para definir qué tan visible será la marca de agua (0 = invisible, 255 = totalmente opaca).
5. **Agregar Marca de Agua.** Pulsa el botón azul. Aparecerá una barra de progreso mientras se procesa cada archivo. Al finalizar se abre automáticamente la carpeta de salida.

### Dónde se guardan los resultados

- **Un solo PDF:** se guarda directamente en la carpeta de destino con el nombre `NOMBRE_marca_de_agua.pdf`.
- **Varios PDFs:** se crea una subcarpeta `Recicley_Watermark_AAAAMMDD_HHMMSS` dentro de la carpeta de destino, con todos los resultados dentro. Si dos archivos de origen tienen el mismo nombre (por ejemplo, provenientes de subcarpetas distintas), se agrega automáticamente `(1)`, `(2)`, etc. para evitar sobrescribirlos.

## Reconstruir el ejecutable

Con Python y las dependencias instaladas:

```
pip install PyQt6 pdf2image PyPDF2 Pillow pyinstaller
python -m PyInstaller GUI_Watermark.spec --noconfirm
```

El resultado queda en `dist/GUI_Watermark/`. `GUI_Watermark.spec` ya está configurado para empaquetar `rec.jpg` y la carpeta `poppler-0.68.0/` dentro del ejecutable, por lo que no hay que copiar nada manualmente.

## Estructura del proyecto

| Archivo / carpeta      | Descripción                                                            |
|-------------------------|--------------------------------------------------------------------------|
| `GUI_Watermark.py`       | Código fuente completo de la aplicación (interfaz + lógica).            |
| `GUI_Watermark.spec`     | Configuración de PyInstaller para generar el `.exe`.                    |
| `rec.jpg`                | Ícono de la ventana / aplicación.                                        |
| `poppler-0.68.0/`        | Binarios de Poppler usados para renderizar páginas de PDF a imagen.     |
| `dist/GUI_Watermark/`    | Resultado del último build: `.exe` + `_internal/` (listo para compartir).|
| `build/`                 | Archivos intermedios de PyInstaller (no se distribuyen).                |

## Documentación técnica

Para una explicación detallada, módulo por módulo y función por función, de cómo funciona el código interno, consulta `Documentacion_Tecnica.pdf`.
