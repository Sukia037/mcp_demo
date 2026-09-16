"""Extract PDF and PPTX text into UTF-8 files for the local knowledge base.

This is a one-time preparation utility. The MCP server reads only the generated
text files, so PDF/PPTX parsing is not part of the demo runtime.
"""

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader


def extract_pdf(path: Path) -> tuple[str, int]:
    reader = PdfReader(path)
    sections = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            sections.append(f"## Page {page_number}\n\n{text}")
    return "\n\n".join(sections), len(reader.pages)


def slide_number(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def extract_pptx(path: Path) -> tuple[str, int]:
    sections = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            (
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=slide_number,
        )
        for name in slide_names:
            root = ElementTree.fromstring(archive.read(name))
            text_runs = [
                (element.text or "").strip()
                for element in root.iter()
                if element.tag.rsplit("}", 1)[-1] == "t" and (element.text or "").strip()
            ]
            if text_runs:
                sections.append(
                    f"## Slide {slide_number(name)}\n\n" + "\n".join(text_runs)
                )
    return "\n\n".join(sections), len(slide_names)


def safe_output_name(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", path.stem).strip("_")
    return f"{stem or 'document'}.txt"


def extract(path: Path) -> tuple[str, int, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text, units = extract_pdf(path)
        return text, units, "pages"
    if suffix == ".pptx":
        text, units = extract_pptx(path)
        return text, units, "slides"
    raise ValueError(f"Unsupported source type: {path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare local RAG text sources.")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("sources", nargs="+", type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for source in args.sources:
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source file not found: {source}")

        text, units, unit_name = extract(source)
        if not text.strip():
            raise ValueError(f"No text could be extracted from: {source.name}")

        output_path = args.output_dir / safe_output_name(source)
        document = f"# {source.stem}\n\nSource: {source.name}\n\n{text}\n"
        output_path.write_text(document, encoding="utf-8")
        results.append(
            {
                "source": source.name,
                "output": output_path.name,
                unit_name: units,
                "characters": len(document),
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

