"""Prepara explícitamente una fotografía pública para pruebas; no se sube a Git."""
import hashlib
from pathlib import Path
from urllib.request import urlopen

URL = 'https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/astronaut.png'
SHA256 = '88431cd9653ccd539741b555fb0a46b61558b301d4110412b5bc28b5e3ea6cb5'
DEST = Path(__file__).resolve().parent / 'imagenes_prueba' / 'astronauta.png'


def main():
    if DEST.exists():
        if hashlib.sha256(DEST.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError('El archivo existente no coincide con la fotografía pública; no se sobrescribe.')
        print('Fotografía pública de prueba verificada; ya está disponible localmente.')
        return
    with urlopen(URL, timeout=30) as response:
        content = response.read(2 * 1024 * 1024)
    if hashlib.sha256(content).hexdigest() != SHA256:
        raise RuntimeError('La descarga no coincide con el SHA-256 esperado; no se guarda.')
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open('xb') as output:
        output.write(content)
    print('Fotografía pública de NASA preparada localmente. Excluida de Git.')


if __name__ == '__main__':
    main()
