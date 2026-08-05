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
- Paquetes: `PyQt6`, `PyPDF2`, `Pillow`, `reportlab`, `cryptography`

No requiere Poppler ni ningún otro binario externo: la marca de agua se superpone directamente sobre cada página (vectorial, sin rasterizar) usando `PyPDF2` + `reportlab`, todo dentro del mismo proceso de Python.

## Instalación / distribución

**La forma más rápida:** entra a la carpeta `GUI_Watermark ejecutable/` y ejecuta `GUI_Watermark.exe` directamente — ya está listo para usar.

> Importante: el `.exe` necesita la carpeta `_internal` a su lado (contiene PyQt6, el ícono y demás dependencias). No lo muevas ni lo copies por separado de esa carpeta.

**La única fuente legítima de una copia es este repositorio de GitHub**
(`Recicley-TI/RecicleyWatermark`, sección Code o Releases). Pero descargarla
de ahí **no alcanza por sí solo**: desde la versión con candado por equipo
(ver [Seguridad y activación](#seguridad-y-activación) abajo), la app no
abre en ningún equipo -sea la primera vez o no- sin un código de activación
que emite Recicley-TI para ese equipo puntual. Copiar la carpeta
`GUI_Watermark ejecutable/` o el `.zip` a otra PC, o simplemente descargarla
de nuevo, **no la deja funcionando** sin ese código.

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

Con Python y las dependencias instaladas, desde la raíz del proyecto:

```
pip install PyQt6 PyPDF2 Pillow reportlab cryptography pyinstaller
python -m PyInstaller app/GUI_Watermark.spec --noconfirm
```

Esto genera `dist/GUI_Watermark/` (el `.exe` + `_internal/`) y una carpeta `build/` con archivos intermedios de PyInstaller — ambas se recrean en cada build y no están versionadas (ver `.gitignore`). `GUI_Watermark.spec` ya está configurado para empaquetar `rec.jpg` dentro del ejecutable, así que no hay que copiar nada manualmente. Cuando el build termine, copia el contenido de `dist/GUI_Watermark/` (el `.exe` + `_internal/`) para reemplazar el de `GUI_Watermark ejecutable/` y así dejar esa carpeta al día.

## Estructura del proyecto

| Carpeta / archivo                    | Descripción                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------|
| `GUI_Watermark ejecutable/`           | **El programa listo para usar** — `.exe` + `_internal/` + zip portable.      |
| `app/GUI_Watermark.py`                | Código fuente completo de la aplicación (interfaz + lógica).                 |
| `app/licensing.py`                    | Candado por equipo: huella de hardware, activación obligatoria, verificación de códigos. |
| `app/GUI_Watermark.spec`              | Configuración de PyInstaller para generar el `.exe`.                         |
| `app/rec.jpg`                         | Ícono de la ventana / aplicación.                                             |
| `admin_tools/`                        | Scripts internos de Recicley-TI para emitir códigos de reactivación (no se distribuyen con el `.exe`). |
| `README.md` *(raíz del proyecto)*     | Documentación general del proyecto — este archivo.                           |
| `docs/Documentacion_Tecnica.pdf`      | Explicación técnica módulo por módulo, función por función.                  |
| `docs/Documentacion_Tecnica_Diagramas.pdf` | Misma documentación técnica, con diagramas.                             |

`build/` y `dist/` (artefactos temporales de PyInstaller) no se versionan — se regeneran solos al reconstruir el ejecutable (ver arriba).

## Seguridad y activación

Desde esta versión, Recicley Watermark tiene un **candado por equipo con
activación obligatoria**: la app **no abre en ningún equipo** -ni siquiera
la primera vez- sin un código de activación emitido por Recicley-TI para
ese equipo puntual (huella de hardware calculada localmente, guardada en
`%LOCALAPPDATA%\Recicley\Watermark\activation.json` una vez activada). Si
esa misma carpeta ya activada se copia y se intenta abrir en otra PC, el
programa también lo detecta y se niega a abrir.

- Es un candado **100% local/offline** en el día a día: una vez activado,
  no llama a ningún servidor ni necesita internet para seguir funcionando.
- **No es DRM irrompible.** Sube la barrera para que ni descargar de
  GitHub ni copiar una carpeta ya usada alcancen por sí solos, pero alguien
  con conocimientos técnicos podría, en teoría, desempacar el `.exe` y
  evitarlo. El objetivo es que "copiar y compartir" (o "descargar y listo")
  dejen de ser la vía normal de distribución, no ofrecer protección militar.
- **Activación (primer uso en un equipo, o después de un cambio de
  hardware):** el programa muestra un **código de máquina** en pantalla.
  Ese código se envía a soporte de Recicley-TI, que genera un **código de
  activación** y se lo devuelve al usuario para pegarlo en el mismo
  diálogo.
- La clave privada usada para firmar códigos de activación
  (`admin_tools/private_key.pem`) vive únicamente en el/los equipo(s) de
  Recicley-TI encargados de soporte y **nunca** se sube al repositorio (ver
  `.gitignore`). Sin esa clave no se pueden emitir códigos de activación
  nuevos, así que conviene respaldarla en un lugar seguro aparte del
  proyecto.

### Generar códigos de activación (uso interno, Recicley-TI)

`admin_tools/` trae dos formas de generar el código de activación a partir
del código de máquina que envía el usuario — ninguna de las dos se sube al
repo (son build/artefactos locales de la máquina de soporte, ver
`.gitignore`):

- **`Recicley_GenerarCodigoActivacion.exe`** (recomendado): doble clic, te
  pide el código de máquina por teclado y te devuelve el código de
  activación. No necesita Python instalado. Se genera una sola vez con
  `python -m PyInstaller admin_tools/generate_unlock_code.spec --noconfirm`
  y debe quedar **en la misma carpeta** que `private_key.pem` (lee la
  clave del disco, al lado del propio `.exe`; no la lleva empaquetada
  adentro).
- **`python admin_tools/generate_unlock_code.py CODIGO-DE-MAQUINA`**: la
  misma herramienta corrida desde el código fuente, para quien prefiera
  usarla así o necesite automatizarla.

## Documentación técnica

Para una explicación detallada, módulo por módulo y función por función, de cómo funciona el código interno, consulta `docs/Documentacion_Tecnica.pdf`.
