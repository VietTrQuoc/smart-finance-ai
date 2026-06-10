"""Convert a simple Marp-style Markdown slide deck to PPTX.

This converter intentionally supports the subset used in this repo's slide
files: headings, bullets, simple tables, code fences, and plain paragraphs.
It avoids external dependencies so the deck can be generated in the local
workspace without installing Office, Pandoc, or python-pptx.
"""

from __future__ import annotations

import argparse
import html
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path


SLIDE_W = 13_333_333
SLIDE_H = 7_500_000


def parse_markdown(path: Path) -> list[list[str]]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^---\s*$", text)
    slides = []
    for block in blocks:
        lines = [line.rstrip() for line in block.strip().splitlines()]
        if not lines:
            continue
        if lines[0].startswith("marp:") or any(line.startswith("theme:") for line in lines[:4]):
            continue
        slides.append(lines)
    return slides


def split_slide(lines: list[str]) -> tuple[str, str, list[str]]:
    title = ""
    subtitle = ""
    body = []
    for line in lines:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## ") and not subtitle:
            subtitle = line[3:].strip()
        else:
            body.append(line)
    return title or "Slide", subtitle, body


def text_runs(text: str) -> str:
    return f"<a:r><a:rPr lang=\"vi-VN\"/><a:t>{html.escape(text)}</a:t></a:r>"


def paragraph(text: str = "", *, level: int = 0, size: int = 2200, bold: bool = False) -> str:
    bullet = ""
    if level > 0:
        bullet = "<a:buChar char=\"•\"/>"
    bold_attr = " b=\"1\"" if bold else ""
    return (
        f"<a:p><a:pPr lvl=\"{max(level - 1, 0)}\">{bullet}"
        f"<a:defRPr sz=\"{size}\"{bold_attr}/></a:pPr>{text_runs(text)}</a:p>"
    )


def body_to_paragraphs(lines: list[str]) -> str:
    paragraphs = []
    in_code = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not line:
            paragraphs.append(paragraph("", size=1400))
            continue
        if in_code:
            paragraphs.append(paragraph(line, size=1800))
            continue
        if line.startswith("|"):
            cleaned = "  ".join(part.strip() for part in line.strip("|").split("|"))
            if set(cleaned.replace(" ", "")) <= {"-", ":"}:
                continue
            paragraphs.append(paragraph(cleaned, size=1650, bold="|" not in raw[:2]))
            continue
        if line.startswith("- "):
            paragraphs.append(paragraph(line[2:].strip(), level=1, size=2000))
            continue
        if re.match(r"^\d+\. ", line):
            paragraphs.append(paragraph(line, level=1, size=2000))
            continue
        if line.startswith("#"):
            cleaned = line.lstrip("#").strip()
            paragraphs.append(paragraph(cleaned, size=2200, bold=True))
            continue
        paragraphs.append(paragraph(line, size=2000))
    return "".join(paragraphs)


def shape_text(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    paragraphs_xml: str,
) -> str:
    return f"""
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="{shape_id}" name="{html.escape(name)}"/>
          <p:cNvSpPr txBox="1"/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" anchor="t"/>
          <a:lstStyle/>
          {paragraphs_xml}
        </p:txBody>
      </p:sp>
    """


def accent_bar() -> str:
    return """
      <p:sp>
        <p:nvSpPr><p:cNvPr id="90" name="Accent"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="0" y="0"/><a:ext cx="180000" cy="7500000"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="167A57"/></a:solidFill>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
      </p:sp>
    """


def slide_xml(lines: list[str], index: int) -> str:
    title, subtitle, body = split_slide(lines)
    if index == 1:
        title_box = shape_text(
            2,
            "Title",
            850_000,
            1_950_000,
            10_900_000,
            1_000_000,
            paragraph(title, size=4400, bold=True),
        )
        subtitle_box = shape_text(
            3,
            "Subtitle",
            870_000,
            3_050_000,
            10_400_000,
            1_000_000,
            paragraph(subtitle, size=2400) + body_to_paragraphs(body[:2]),
        )
    else:
        title_box = shape_text(
            2,
            "Title",
            700_000,
            420_000,
            11_900_000,
            650_000,
            paragraph(title, size=3100, bold=True),
        )
        subtitle_box = shape_text(
            3,
            "Body",
            820_000,
            1_300_000,
            11_650_000,
            5_600_000,
            (paragraph(subtitle, size=2300, bold=True) if subtitle else "") + body_to_paragraphs(body),
        )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="F5F4EF"/></a:solidFill></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {accent_bar()}
      {title_box}
      {subtitle_box}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def presentation_xml(slide_count: int) -> str:
    slide_ids = "\n".join(
        f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>' for i in range(slide_count)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{slide_count + 1}"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def presentation_rels(slide_count: int) -> str:
    rels = []
    for i in range(slide_count):
        rels.append(
            f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{''.join(rels)}
</Relationships>"""


def content_types(slide_count: int) -> str:
    slides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  {slides}
</Types>"""


def static_files(slide_count: int) -> dict[str, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>""",
        "docProps/core.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Canvas Design</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>""",
        "docProps/app.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Markdown PPTX Converter</Application>
  <PresentationFormat>Widescreen</PresentationFormat>
  <Slides>{slide_count}</Slides>
</Properties>""",
        "ppt/theme/theme1.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Simple">
  <a:themeElements>
    <a:clrScheme name="Simple">
      <a:dk1><a:srgbClr val="17201C"/></a:dk1><a:lt1><a:srgbClr val="F5F4EF"/></a:lt1>
      <a:dk2><a:srgbClr val="65716B"/></a:dk2><a:lt2><a:srgbClr val="FFFFFF"/></a:lt2>
      <a:accent1><a:srgbClr val="167A57"/></a:accent1><a:accent2><a:srgbClr val="B87916"/></a:accent2>
      <a:accent3><a:srgbClr val="0F6F7C"/></a:accent3><a:accent4><a:srgbClr val="B63C32"/></a:accent4>
      <a:accent5><a:srgbClr val="385F8F"/></a:accent5><a:accent6><a:srgbClr val="ECE9DF"/></a:accent6>
      <a:hlink><a:srgbClr val="0F6F7C"/></a:hlink><a:folHlink><a:srgbClr val="B63C32"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Simple"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Simple"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme>
  </a:themeElements>
</a:theme>""",
        "ppt/slideMasters/slideMaster1.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>""",
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>""",
        "ppt/slideLayouts/slideLayout1.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
</p:sldLayout>""",
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>""",
    }


def write_pptx(markdown_path: Path, output_path: Path) -> None:
    slides = parse_markdown(markdown_path)
    if not slides:
        raise ValueError(f"No slides found in {markdown_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", content_types(len(slides)))
        package.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        package.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        for name, content in static_files(len(slides)).items():
            package.writestr(name, content)
        for index, lines in enumerate(slides, start=1):
            package.writestr(f"ppt/slides/slide{index}.xml", slide_xml(lines, index))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Markdown slides to PPTX")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_pptx(args.input, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
