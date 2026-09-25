import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(root: Path) -> None:
    directory = root / "logs"
    directory.mkdir(exist_ok=True)
    logger = logging.getLogger("studyai")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = RotatingFileHandler(directory / "studyai.log", maxBytes=1_000_000,
                                      backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    # Não habilitar debug HTTP: ele pode incluir conteúdo das requisições.
    for name in ("openai", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
