"""Genera un código de activación para un equipo.

Uso interno de Recicley-TI. La app NUNCA se auto-activa sola (ver
app/licensing.py) — así que este script hace falta en dos situaciones, no
solo una:

  1. Alguien va a usar Recicley Watermark por PRIMERA VEZ en un equipo
     (recién descargado de GitHub, o cualquier copia).
  2. Un equipo que ya estaba activado cambió de hardware (reinstaló
     Windows, cambió de disco, etc.) y quedó bloqueado de nuevo.

En ambos casos la app le muestra al usuario el mismo "código de máquina"
en pantalla, que te va a pasar por el canal de soporte que usen.

Dos formas de correrlo:

  - Como .exe (Recicley_GenerarCodigoActivacion.exe, ver
    generate_unlock_code.spec): doble clic y te lo pide por teclado. No
    necesita Python instalado en la máquina de soporte.
  - Como script, pasando el código directo:
        python admin_tools/generate_unlock_code.py CODIGO-DE-MAQUINA

En ambos casos imprime un código de activación para pegarle de vuelta al
usuario en el diálogo de la app.

OJO: "CODIGO-DE-MAQUINA" es el texto exacto que el usuario ve y copia del
campo "Código de máquina" en el diálogo de bloqueo (ej.
"K7QY-4XZP-2M3N-8FQR") — NO el hash sha256 completo interno. Firmamos ese
código corto porque es lo único que efectivamente viaja entre el usuario y
soporte, y app/licensing.py verifica la firma contra ese mismo texto.
Cópialo tal cual te lo pasen (mayúsculas y guiones incluidos).

Requiere private_key.pem al lado de este script (o del .exe, si lo usas
empaquetado) — generado una sola vez con generate_keypair.py. Ese archivo
NUNCA debe subirse al repo ni distribuirse: solo debe existir en la(s)
máquina(s) de soporte de Recicley-TI.
"""
import base64
import os
import sys

from cryptography.hazmat.primitives.serialization import load_pem_private_key


def _here():
    # Congelado (PyInstaller onefile): al lado del .exe real, no de la
    # carpeta temporal donde se descomprime en cada arranque (_MEIPASS) —
    # así private_key.pem puede vivir permanentemente junto al .exe.
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


HERE = _here()
PRIVATE_KEY_PATH = os.path.join(HERE, "private_key.pem")


def _load_private_key():
    if not os.path.exists(PRIVATE_KEY_PATH):
        print(f"No se encontró private_key.pem junto a este programa ({HERE}).")
        print("Corre primero generate_keypair.py (una sola vez) y colócalo ahí.")
        return None
    with open(PRIVATE_KEY_PATH, "rb") as f:
        return load_pem_private_key(f.read(), password=None)


def _sign(private_key, machine_code_str):
    signature = private_key.sign(machine_code_str.encode("ascii"))
    return base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")


def main():
    private_key = _load_private_key()
    if private_key is None:
        sys.exit(1)

    if len(sys.argv) == 2:
        machine_code_str = sys.argv[1].strip()
    elif len(sys.argv) == 1:
        print("Recicley Watermark - Generador de códigos de activación")
        print("=" * 55)
        try:
            machine_code_str = input(
                "Pega el código de máquina que te pasó el usuario: ").strip()
        except EOFError:
            machine_code_str = ""
    else:
        print("Uso: generate_unlock_code CODIGO-DE-MAQUINA")
        print("(o sin argumentos, para que te lo pida por teclado)")
        sys.exit(1)

    if not machine_code_str:
        print("No se ingresó ningún código.")
        sys.exit(1)

    unlock_code = _sign(private_key, machine_code_str)

    print()
    print("Código de activación (pégalo en la app del usuario):")
    print(unlock_code)

    if getattr(sys, "frozen", False):
        try:
            input("\nPresiona Enter para salir...")
        except EOFError:
            pass


if __name__ == "__main__":
    main()
