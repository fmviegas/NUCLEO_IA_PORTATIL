"""Gravação com substituição atômica por arquivo."""
import os
import tempfile

def _gravar_atomico(destino, gravar):
    fd, temp = tempfile.mkstemp(prefix=".diagramador-", dir=os.path.dirname(os.path.abspath(destino)))
    os.close(fd)
    try:
        gravar(temp)
        os.replace(temp, destino)
    finally:
        if os.path.exists(temp):
            os.remove(temp)

