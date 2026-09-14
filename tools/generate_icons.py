from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from deployment_manager.icons import write_icon_assets


def main() -> int:
    app = QApplication.instance() or QApplication([])
    png_path, ico_path = write_icon_assets(ROOT / "assets", overwrite=True)
    print(f"Created {png_path}")
    print(f"Created {ico_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
