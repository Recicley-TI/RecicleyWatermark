"""Candado por equipo (node-lock) para Recicley Watermark.

Qué hace y qué NO hace
-----------------------
Esta app se distribuye como carpeta portable, sin instalador. El candado es
100% offline: no llama a ningún servidor ni depende de tener internet para
funcionar día a día. La activación NO es automática en ningún caso -ni
siquiera la primera vez que se corre en una PC-: siempre hace falta un
código emitido por Recicley-TI (admin_tools/generate_unlock_code.py) para
que la app abra en un equipo. Es deliberado: si el primer arranque se
auto-activara solo, cualquiera que reciba una copia sin estrenar -reenviada
por otra persona, sin pasar por GitHub- podría usarla con solo abrirla, y
el candado no serviría de nada.

Esto SUBE LA BARRERA (nadie puede usar una copia, ni nueva ni ya usada, sin
que Recicley-TI le entregue un código para ese equipo puntual), pero no es
DRM irrompible: esta app es Python empaquetado con PyInstaller, que alguien
con conocimientos técnicos puede desempacar y leer, incluida la clave HMAC
local de este archivo. El objetivo es que "copiar la carpeta y listo" -o
"descargarla y listo"- dejen de ser suficiente, no volver la app
inhackeable. La única fuente legítima de una copia nueva sigue siendo el
repo de GitHub, pero descargarla ya no alcanza por sí sola:
https://github.com/Recicley-TI/RecicleyWatermark

Flujo
-----
1. Primer arranque en una PC (o cualquier arranque en una PC cuyo hardware
   cambió, o cuyo archivo de activación está dañado/manipulado): no hay un
   registro de activación válido para esa huella de hardware -> la app se
   bloquea y muestra un "código de máquina".
2. El usuario envía ese código a Recicley-TI (correo/whatsapp/etc.).
3. Recicley-TI firma ese código con la clave privada -que NUNCA sale de
   admin_tools/, ver generate_unlock_code.py- y entrega un "código de
   activación" de vuelta.
4. El usuario lo pega en el diálogo de bloqueo. Se verifica con la clave
   pública embebida más abajo; si es válida, se guarda localmente firmada
   con la huella de esa PC y la app abre normal desde entonces.
5. Arranques siguientes en la misma PC: la huella sigue coincidiendo con lo
   guardado en el paso 4 -> abre normal, sin pedir nada de nuevo.
"""
import base64
import ctypes
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

try:
    import winreg
except ImportError:  # no-Windows (solo relevante para pruebas locales)
    winreg = None

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QVBoxLayout,
)

GITHUB_URL = "https://github.com/Recicley-TI/RecicleyWatermark"

APP_SALT = b"Recicley-Watermark-v1"

# Clave pública correspondiente a admin_tools/private_key.pem, que SOLO
# tiene Recicley-TI. Generada una única vez con
# admin_tools/generate_keypair.py. Es una clave PÚBLICA: no hay problema en
# que viva en el código / dentro del .exe que reciben los usuarios.
PUBLIC_KEY_HEX = "9e401e7f16cbd24654f892bb7e66df770c78c835c7b97ae31dbd96de7a9a134e"

# Clave para el HMAC que protege el archivo de activación LOCAL contra
# edición manual casual. No es un secreto fuerte (ver docstring del
# módulo) — solo evita que alguien abra el .json y cambie el hwid a mano.
_LOCAL_HMAC_KEY = bytes.fromhex(
    "726386a02b2070e9b34a495e4d0a35311522fc87aab99ab69bb2e081d99d3f73")


# --- Huella de hardware ------------------------------------------------

def _machine_guid():
    if winreg is None:
        return ""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        try:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return value
        finally:
            winreg.CloseKey(key)
    except OSError:
        return ""


def _volume_serial():
    try:
        system_drive = os.environ.get("SystemDrive", "C:") + "\\"
        volume_name_buf = ctypes.create_unicode_buffer(261)
        fs_name_buf = ctypes.create_unicode_buffer(261)
        serial = ctypes.c_uint(0)
        max_component_len = ctypes.c_uint(0)
        fs_flags = ctypes.c_uint(0)
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(system_drive),
            volume_name_buf, ctypes.sizeof(volume_name_buf),
            ctypes.byref(serial),
            ctypes.byref(max_component_len),
            ctypes.byref(fs_flags),
            fs_name_buf, ctypes.sizeof(fs_name_buf),
        )
        return f"{serial.value:08X}" if ok else ""
    except (AttributeError, OSError):
        return ""


def hardware_id():
    """Huella determinística del equipo actual (sha256 hex, 64 chars)."""
    parts = "|".join([
        _machine_guid(),
        _volume_serial(),
        os.environ.get("COMPUTERNAME", ""),
    ])
    return hashlib.sha256(APP_SALT + parts.encode("utf-8", "ignore")).hexdigest()


def machine_code(hwid_hex=None):
    """Versión corta y legible del hwid, para mostrar/comunicar por texto."""
    hwid_hex = hwid_hex or hardware_id()
    raw = bytes.fromhex(hwid_hex)[:10]
    b32 = base64.b32encode(raw).decode("ascii").rstrip("=")
    return "-".join(b32[i:i + 4] for i in range(0, len(b32), 4))


# --- Registro de activación local --------------------------------------

def _activation_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "Recicley", "Watermark")
    os.makedirs(path, exist_ok=True)
    return path


def _activation_path():
    return os.path.join(_activation_dir(), "activation.json")


def _sign_record(hwid, activated_at):
    msg = f"{hwid}|{activated_at}".encode("utf-8")
    return hmac.new(_LOCAL_HMAC_KEY, msg, hashlib.sha256).hexdigest()


def _save_activation(hwid):
    activated_at = datetime.now(timezone.utc).isoformat()
    record = {
        "hwid": hwid,
        "activated_at": activated_at,
        "mac": _sign_record(hwid, activated_at),
    }
    with open(_activation_path(), "w", encoding="utf-8") as f:
        json.dump(record, f)
    return record


def _load_activation():
    """None = no activado todavía. "corrupted" = archivo dañado/manipulado.
    dict = registro válido."""
    path = _activation_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        expected = _sign_record(record["hwid"], record["activated_at"])
        if not hmac.compare_digest(expected, record.get("mac", "")):
            return "corrupted"
        return record
    except (json.JSONDecodeError, KeyError, OSError, ValueError):
        return "corrupted"


class ActivationStatus:
    ALLOWED = "allowed"
    BLOCKED_NOT_ACTIVATED = "blocked_not_activated"
    BLOCKED_MISMATCH = "blocked_mismatch"
    BLOCKED_CORRUPTED = "blocked_corrupted"


def check_status():
    """Devuelve (status, hwid_actual).

    NO hay auto-activación: un equipo que nunca recibió un código de
    Recicley-TI queda bloqueado igual que uno con la huella de otro
    equipo. Esto es deliberado — ver docstring del módulo: si el primer
    arranque se auto-activara solo, cualquiera que reciba una copia sin
    estrenar (por ejemplo reenviada por otra persona, sin pasar por
    GitHub) podría usarla con solo abrirla. Exigir siempre un código
    emitido por Recicley-TI (admin_tools/generate_unlock_code.py) cierra
    ese hueco.
    """
    current = hardware_id()
    record = _load_activation()
    if record is None:
        return ActivationStatus.BLOCKED_NOT_ACTIVATED, current
    if record == "corrupted":
        return ActivationStatus.BLOCKED_CORRUPTED, current
    if record["hwid"] == current:
        return ActivationStatus.ALLOWED, current
    return ActivationStatus.BLOCKED_MISMATCH, current


# --- Reactivación (firma asimétrica Ed25519) ----------------------------

def _b64url_decode(s):
    s = "".join(s.split())  # tolera espacios/saltos de línea al pegar
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def verify_unlock_code(code, hwid=None):
    """True si `code` es una firma válida (de Recicley-TI) para este hwid.

    Se firma/verifica sobre el `machine_code` (el código CORTO que se
    muestra en pantalla y que el usuario transcribe a soporte), no sobre el
    hash completo de 64 caracteres: es lo único que efectivamente viaja
    entre el usuario y Recicley-TI, así que tiene que ser lo mismo que
    admin_tools/generate_unlock_code.py firma del otro lado.
    """
    hwid = hwid or hardware_id()
    try:
        signature = _b64url_decode(code)
        public_key = Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(PUBLIC_KEY_HEX))
        public_key.verify(signature, machine_code(hwid).encode("ascii"))
        return True
    except Exception:
        return False


def import_unlock_code(code):
    """Si el código es válido para este equipo, re-activa localmente."""
    current = hardware_id()
    if verify_unlock_code(code, current):
        _save_activation(current)
        return True
    return False


# --- Diálogo de bloqueo (PyQt6) ------------------------------------------

class _ActivationBlockedDialog(QDialog):
    def __init__(self, reason, code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recicley Watermark - Equipo no autorizado")
        self.setFixedWidth(440)
        self.unlocked = False

        layout = QVBoxLayout(self)

        if reason == ActivationStatus.BLOCKED_NOT_ACTIVATED:
            explanation = (
                "Este equipo todavía no está activado. Recicley Watermark "
                "requiere un código de activación antes del primer uso en "
                "cada equipo, así que descargarlo o copiarlo no alcanza por "
                "sí solo."
            )
        elif reason == ActivationStatus.BLOCKED_CORRUPTED:
            explanation = (
                "El archivo de activación de este equipo está dañado o fue "
                "modificado."
            )
        else:
            explanation = (
                "Esta copia de Recicley Watermark ya está vinculada a otro "
                "equipo y no puede usarse aquí."
            )
        explanation += (
            "\n\nEnvía el código de máquina de abajo a soporte de "
            "Recicley-TI para obtener un código de activación.\n\n"
            f"¿No tienes el programa todavía? Descárgalo desde:\n{GITHUB_URL}"
        )
        label = QLabel(explanation, self)
        label.setWordWrap(True)
        layout.addWidget(label)

        layout.addWidget(QLabel("Código de máquina:", self))
        code_field = QLineEdit(code, self)
        code_field.setReadOnly(True)
        layout.addWidget(code_field)

        layout.addWidget(QLabel("Código de activación:", self))
        self.unlock_input = QLineEdit(self)
        self.unlock_input.setPlaceholderText(
            "Pega aquí el código que te dio soporte")
        layout.addWidget(self.unlock_input)

        buttons = QHBoxLayout()
        verify_btn = QPushButton("Verificar código", self)
        verify_btn.clicked.connect(self._on_verify)
        exit_btn = QPushButton("Salir", self)
        exit_btn.clicked.connect(self.reject)
        buttons.addWidget(verify_btn)
        buttons.addWidget(exit_btn)
        layout.addLayout(buttons)

    def _on_verify(self):
        code = self.unlock_input.text()
        if code and import_unlock_code(code):
            self.unlocked = True
            self.accept()
        else:
            QMessageBox.warning(
                self, "Código inválido",
                "Ese código de activación no es válido para este equipo.")


def ensure_activated(parent=None):
    """Punto de entrada: True si la app puede abrir en este equipo.

    No hay auto-activación (ver docstring del módulo): si el equipo no
    tiene ya un registro de activación válido -sea porque nunca se activó,
    porque el hardware cambió, o porque el archivo local fue manipulado-
    se muestra el diálogo de bloqueo (con opción de pegar un código de
    activación) y se devuelve el resultado de esa interacción.
    """
    status, hwid = check_status()
    if status == ActivationStatus.ALLOWED:
        return True

    dialog = _ActivationBlockedDialog(status, machine_code(hwid), parent)
    dialog.exec()
    return dialog.unlocked
