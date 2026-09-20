from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_dir: Path, level_name: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "convertflow.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
