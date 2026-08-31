"""Genera el par de claves Ed25519 usado para firmar códigos de reactivación.

Uso único: se corre una sola vez, al configurar el sistema de activación por
primera vez (o si algún día se decide rotar la clave). Genera:

  - admin_tools/private_key.pem  -> SOLO para Recicley-TI. NUNCA se sube al
    repo (ver .gitignore). Sin este archivo no se pueden generar códigos de
    reactivación nuevos, así que hay que respaldarlo en un lugar seguro
    (gestor de contraseñas, USB cifrado, etc.) fuera de este proyecto.

  - La clave PÚBLICA se imprime en pantalla en formato hex, lista para
    pegarse en la constante PUBLIC_KEY_HEX de app/licensing.py. Esa clave sí
    es pública: va embebida en el .exe que reciben todos los usuarios.

Ejecutar desde la raíz del proyecto:
    python admin_tools/generate_keypair.py
"""
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

HERE = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_PATH = os.path.join(HERE, "private_key.pem")


def main():
    if os.path.exists(PRIVATE_KEY_PATH):
        print(f"Ya existe {PRIVATE_KEY_PATH}.")
        print("Si de verdad quieres generar una clave nueva (esto invalida")
        print("todos los códigos de reactivación emitidos hasta ahora),")
        print("borra ese archivo a mano y vuelve a correr este script.")
        return

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(private_bytes)

    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    print("Clave privada guardada en:", PRIVATE_KEY_PATH)
    print("(NO se sube al repo — respáldala en un lugar seguro aparte)")
    print()
    print("Clave pública (pégala en PUBLIC_KEY_HEX dentro de app/licensing.py):")
    print(public_bytes.hex())


if __name__ == "__main__":
    main()
