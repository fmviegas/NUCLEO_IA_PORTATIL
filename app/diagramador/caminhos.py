import os
import re

def _resolver_caminho(base_dir: str, src: str) -> str:
    """Resolve o caminho de uma imagem relativo ao arquivo-fonte."""
    if re.match(r"^[a-z]+://", src) or os.path.isabs(src):
        return src
    return os.path.normpath(os.path.join(base_dir or ".", src))

