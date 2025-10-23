import sys
from pathlib import Path
from typing import Iterable

from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

# Convert all SVGs in resources/icons to PNG variants for packaging compatibility
# Outputs to resources/icons_png with default size variants

SIZES: Iterable[int] = (64, 128, 256)


def convert_svg(svg_path: Path, out_dir: Path) -> None:
    if svg_path.stat().st_size == 0:
        print(f"Skipping empty SVG: {svg_path}")
        return

    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        print(f"Invalid SVG, skipping: {svg_path}")
        return

    for size in SIZES:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        output_path = out_dir / f"{svg_path.stem}_{size}.png"
        image.save(str(output_path))


def main() -> None:
    app = QGuiApplication(sys.argv)
    src_dir = Path(__file__).resolve().parents[1] / "resources" / "icons"
    out_dir = Path(__file__).resolve().parents[1] / "resources" / "icons_png"
    out_dir.mkdir(parents=True, exist_ok=True)
    for svg in src_dir.glob("*.svg"):
        convert_svg(svg, out_dir)


if __name__ == "__main__":
    main()
