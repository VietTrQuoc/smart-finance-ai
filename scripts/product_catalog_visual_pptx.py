"""Create a visual PowerPoint deck for the product catalog.

The script writes PPTX OpenXML directly so it can run in this repository
without installing Office, Pandoc, Marp, or python-pptx.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


SLIDE_W = 13_333_333
SLIDE_H = 7_500_000

BG = "F4F0E8"
INK = "1A2620"
MUTED = "69746E"
GREEN = "167A57"
GREEN_DARK = "0D513C"
MINT = "DDEBE2"
AMBER = "D4922D"
AMBER_LIGHT = "F7E4BF"
RED = "B74337"
RED_LIGHT = "F3CFC9"
BLUE = "2B6777"
BLUE_LIGHT = "D9EAF0"
CARD = "FFFDF8"
LINE = "D7D0C4"
CREAM = "ECE5D8"

TYPE_TITLE = "Aptos Display"
TYPE_BODY = "Aptos"


def emu(value: float) -> int:
    return int(value)


def xml(text: object) -> str:
    return escape(str(text), {'"': "&quot;"})


def srgb(color: str, alpha: int | None = None) -> str:
    if alpha is None:
        return f'<a:srgbClr val="{color}"/>'
    return f'<a:srgbClr val="{color}"><a:alpha val="{alpha}"/></a:srgbClr>'


def solid_fill(color: str, alpha: int | None = None) -> str:
    return f"<a:solidFill>{srgb(color, alpha)}</a:solidFill>"


def line_xml(color: str | None = LINE, width: int = 12_700, alpha: int | None = None) -> str:
    if color is None:
        return "<a:ln><a:noFill/></a:ln>"
    return f'<a:ln w="{width}">{solid_fill(color, alpha)}</a:ln>'


def no_fill() -> str:
    return "<a:noFill/>"


def run_xml(
    text: str,
    *,
    size: int,
    color: str = INK,
    bold: bool = False,
    typeface: str = TYPE_BODY,
) -> str:
    bold_attr = ' b="1"' if bold else ""
    return (
        f'<a:r><a:rPr lang="vi-VN" sz="{size}"{bold_attr}>'
        f"{solid_fill(color)}"
        f'<a:latin typeface="{xml(typeface)}"/><a:cs typeface="{xml(typeface)}"/>'
        f"</a:rPr><a:t>{xml(text)}</a:t></a:r>"
    )


def paragraph_xml(
    text: str = "",
    *,
    size: int = 1800,
    color: str = INK,
    bold: bool = False,
    align: str = "l",
    typeface: str = TYPE_BODY,
    bullet: bool = False,
    space_after: int = 600,
) -> str:
    bullet_xml = ""
    mar = ""
    if bullet:
        bullet_xml = '<a:buChar char="•"/>'
        mar = ' marL="260000" indent="-180000"'
    return (
        f'<a:p><a:pPr algn="{align}"{mar}>'
        f'<a:spcAft><a:spcPts val="{space_after}"/></a:spcAft>'
        f"{bullet_xml}"
        f'<a:defRPr sz="{size}">{solid_fill(color)}'
        f'<a:latin typeface="{xml(typeface)}"/><a:cs typeface="{xml(typeface)}"/></a:defRPr>'
        f"</a:pPr>"
        f"{run_xml(text, size=size, color=color, bold=bold, typeface=typeface)}"
        f"</a:p>"
    )


def paragraphs_xml(items: list[dict[str, object] | str]) -> str:
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(paragraph_xml(item))
        else:
            result.append(paragraph_xml(**item))
    return "".join(result)


class Slide:
    def __init__(self, title: str | None = None, section: str | None = None) -> None:
        self.title = title
        self.section = section
        self.parts: list[str] = []
        self.shape_id = 1

    def next_id(self) -> int:
        self.shape_id += 1
        return self.shape_id

    def background(self, color: str = BG) -> str:
        return f'<p:bg><p:bgPr>{solid_fill(color)}</p:bgPr></p:bg>'

    def shape(
        self,
        *,
        name: str,
        x: int,
        y: int,
        w: int,
        h: int,
        fill: str | None = CARD,
        line: str | None = LINE,
        prst: str = "roundRect",
        alpha: int | None = None,
        line_alpha: int | None = None,
        line_width: int = 12_700,
        text: str | None = None,
        text_size: int = 1800,
        text_color: str = INK,
        bold: bool = False,
        align: str = "ctr",
        valign: str = "mid",
        typeface: str = TYPE_BODY,
        inset: int = 110_000,
    ) -> None:
        text_body = ""
        if text is not None:
            text_body = (
                "<p:txBody>"
                f'<a:bodyPr wrap="square" anchor="{valign}" lIns="{inset}" tIns="{inset}" rIns="{inset}" bIns="{inset}"/>'
                "<a:lstStyle/>"
                + paragraph_xml(
                    text,
                    size=text_size,
                    color=text_color,
                    bold=bold,
                    align=align,
                    typeface=typeface,
                    space_after=0,
                )
                + "</p:txBody>"
            )
        fill_xml = no_fill() if fill is None else solid_fill(fill, alpha)
        self.parts.append(
            f"""
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{self.next_id()}" name="{xml(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
          <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>
          {fill_xml}
          {line_xml(line, line_width, line_alpha)}
        </p:spPr>
        {text_body}
      </p:sp>
    """
        )

    def text_box(
        self,
        *,
        name: str,
        x: int,
        y: int,
        w: int,
        h: int,
        paragraphs: list[dict[str, object] | str],
        valign: str = "t",
        inset: int = 0,
    ) -> None:
        self.parts.append(
            f"""
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{self.next_id()}" name="{xml(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" anchor="{valign}" lIns="{inset}" tIns="{inset}" rIns="{inset}" bIns="{inset}"/>
          <a:lstStyle/>
          {paragraphs_xml(paragraphs)}
        </p:txBody>
      </p:sp>
    """
        )

    def line(self, *, x: int, y: int, w: int, h: int, color: str = LINE, width: int = 18_000) -> None:
        self.shape(name="Line", x=x, y=y, w=w, h=h, fill=color, line=None, prst="rect")

    def arrow(self, *, x: int, y: int, w: int, h: int, color: str = GREEN) -> None:
        self.shape(name="Arrow", x=x, y=y, w=w, h=h, fill=color, line=None, prst="rightArrow")

    def header(self, title: str, kicker: str | None = None) -> None:
        if kicker:
            self.text_box(
                name="Kicker",
                x=720_000,
                y=380_000,
                w=10_500_000,
                h=220_000,
                paragraphs=[
                    {
                        "text": kicker.upper(),
                        "size": 950,
                        "color": GREEN,
                        "bold": True,
                        "space_after": 0,
                    }
                ],
            )
            title_y = 640_000
        else:
            title_y = 420_000
        self.text_box(
            name="Title",
            x=700_000,
            y=title_y,
            w=11_900_000,
            h=520_000,
            paragraphs=[
                {
                    "text": title,
                    "size": 2850,
                    "color": INK,
                    "bold": True,
                    "typeface": TYPE_TITLE,
                    "space_after": 0,
                }
            ],
        )

    def footer(self, index: int, total: int) -> None:
        self.shape(name="Footer line", x=700_000, y=7_090_000, w=11_900_000, h=18_000, fill=LINE, line=None, prst="rect", alpha=70000)
        self.text_box(
            name="Slide number",
            x=11_760_000,
            y=7_140_000,
            w=820_000,
            h=170_000,
            paragraphs=[
                {
                    "text": f"{index:02d}/{total:02d}",
                    "size": 850,
                    "color": MUTED,
                    "align": "r",
                    "space_after": 0,
                }
            ],
        )

    def to_xml(self, index: int, total: int, *, footer: bool = True) -> str:
        if footer:
            self.footer(index, total)
        content = "\n".join(self.parts)
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    {self.background()}
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {content}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def load_catalog(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def label_product_type(value: str) -> str:
    labels = {
        "credit_card": "Credit Card",
        "insurance": "Insurance",
        "loan": "Loan",
        "saving": "Saving",
        "investment": "Investment",
        "pension": "Pension",
        "service": "Service",
    }
    return labels.get(value, value.replace("_", " ").title())


def product_summary(products: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    type_counts = Counter(str(p["product_type"]) for p in products)
    risk_counts = Counter(str(p["risk_allowed"]) for p in products)
    examples = defaultdict(list)
    for product in products:
        product_type = str(product["product_type"])
        if len(examples[product_type]) < 2:
            examples[product_type].append(str(product["product_name"]))

    groups = [
        {
            "label": label_product_type(key),
            "count": type_counts[key],
            "examples": ", ".join(examples[key]),
        }
        for key in sorted(type_counts, key=lambda item: (-type_counts[item], item))
    ]
    risk_order = ["low", "medium", "high"]
    risks = [
        {
            "risk": risk,
            "label": risk.title(),
            "count": risk_counts[risk],
        }
        for risk in risk_order
    ]
    return groups, risks


def add_metric_card(slide: Slide, x: int, y: int, w: int, h: int, value: str, label: str, color: str) -> None:
    slide.shape(name=f"Metric {label}", x=x, y=y, w=w, h=h, fill=CARD, line=LINE, prst="roundRect")
    slide.shape(name=f"Metric dot {label}", x=x + 160_000, y=y + 170_000, w=170_000, h=170_000, fill=color, line=None, prst="ellipse")
    slide.text_box(
        name=f"Metric value {label}",
        x=x + 190_000,
        y=y + 420_000,
        w=w - 380_000,
        h=580_000,
        paragraphs=[
            {"text": value, "size": 3600, "color": color, "bold": True, "typeface": TYPE_TITLE, "align": "ctr", "space_after": 0}
        ],
    )
    slide.text_box(
        name=f"Metric label {label}",
        x=x + 210_000,
        y=y + 1_070_000,
        w=w - 420_000,
        h=300_000,
        paragraphs=[{"text": label, "size": 1150, "color": MUTED, "align": "ctr", "space_after": 0}],
    )


def cover_slide(products: list[dict[str, object]], groups: list[dict[str, object]], risks: list[dict[str, object]]) -> Slide:
    slide = Slide()
    slide.shape(name="Hero dark", x=0, y=0, w=SLIDE_W, h=SLIDE_H, fill=INK, line=None, prst="rect")
    slide.shape(name="Orb green", x=9_000_000, y=-1_500_000, w=4_800_000, h=4_800_000, fill=GREEN, line=None, prst="ellipse", alpha=43000)
    slide.shape(name="Orb amber", x=-900_000, y=4_950_000, w=3_200_000, h=3_200_000, fill=AMBER, line=None, prst="ellipse", alpha=36000)
    slide.shape(name="Soft grid 1", x=7_500_000, y=4_820_000, w=4_900_000, h=32_000, fill="FFFFFF", line=None, prst="rect", alpha=18000)
    slide.shape(name="Soft grid 2", x=8_100_000, y=5_420_000, w=3_800_000, h=32_000, fill="FFFFFF", line=None, prst="rect", alpha=15000)
    slide.text_box(
        name="Kicker",
        x=820_000,
        y=830_000,
        w=4_700_000,
        h=260_000,
        paragraphs=[{"text": "SMART FINANCE AI", "size": 1050, "color": "A7D7BF", "bold": True, "space_after": 0}],
    )
    slide.text_box(
        name="Hero title",
        x=800_000,
        y=1_280_000,
        w=7_400_000,
        h=1_520_000,
        paragraphs=[
            {"text": "Product Catalog", "size": 5300, "color": "FFFFFF", "bold": True, "typeface": TYPE_TITLE, "space_after": 0},
            {"text": "Danh mục sản phẩm cho hệ thống gợi ý tài chính", "size": 1750, "color": "DDEBE2", "space_after": 0},
        ],
    )
    slide.text_box(
        name="Hero body",
        x=840_000,
        y=3_050_000,
        w=6_400_000,
        h=780_000,
        paragraphs=[
            {
                "text": "Mục tiêu: chọn đúng sản phẩm cho từng khách hàng dựa trên hành vi, rủi ro và ưu tiên chiến dịch.",
                "size": 1500,
                "color": "F4F0E8",
                "space_after": 0,
            }
        ],
    )
    card_y = 4_420_000
    add_metric_card(slide, 820_000, card_y, 2_300_000, 1_520_000, str(len(products)), "sản phẩm", GREEN)
    add_metric_card(slide, 3_430_000, card_y, 2_300_000, 1_520_000, str(len(groups)), "nhóm", BLUE)
    add_metric_card(slide, 6_040_000, card_y, 2_300_000, 1_520_000, str(len([r for r in risks if int(r["count"]) > 0])), "mức rủi ro", AMBER)
    slide.shape(name="Hero card", x=8_880_000, y=1_310_000, w=3_560_000, h=4_520_000, fill="FFFDF8", line=None, prst="roundRect")
    slide.text_box(
        name="Mini map title",
        x=9_210_000,
        y=1_690_000,
        w=2_900_000,
        h=370_000,
        paragraphs=[{"text": "Catalog map", "size": 1650, "color": INK, "bold": True, "typeface": TYPE_TITLE, "align": "ctr", "space_after": 0}],
    )
    for idx, risk in enumerate(risks):
        colors = {"low": GREEN, "medium": AMBER, "high": RED}
        y = 2_340_000 + idx * 830_000
        slide.shape(name=f"Risk ring {risk['label']}", x=9_250_000, y=y, w=550_000, h=550_000, fill=colors[str(risk["risk"])], line=None, prst="ellipse", alpha=85000)
        slide.text_box(
            name=f"Risk count {risk['label']}",
            x=9_250_000,
            y=y + 125_000,
            w=550_000,
            h=220_000,
            paragraphs=[{"text": str(risk["count"]), "size": 1500, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}],
        )
        slide.text_box(
            name=f"Risk label {risk['label']}",
            x=10_020_000,
            y=y + 85_000,
            w=1_820_000,
            h=330_000,
            paragraphs=[{"text": f"{risk['label']} risk", "size": 1250, "color": INK, "bold": True, "space_after": 0}],
        )
    return slide


def four_questions_slide() -> Slide:
    slide = Slide()
    slide.header("Product Catalog là gì?", "Ý tưởng chính")
    slide.text_box(
        name="Intro",
        x=780_000,
        y=1_250_000,
        w=9_800_000,
        h=420_000,
        paragraphs=[
            {
                "text": "Catalog là “bộ nhớ sản phẩm” kiêm “luật kinh doanh” để recommendation không gợi ý bừa.",
                "size": 1550,
                "color": MUTED,
                "space_after": 0,
            }
        ],
    )
    cards = [
        ("01", "Có sản phẩm nào?", "Danh sách offer đang active", GREEN),
        ("02", "Dành cho ai?", "Hành vi và tín hiệu mục tiêu", BLUE),
        ("03", "Rủi ro thế nào?", "Low, Medium hoặc High", AMBER),
        ("04", "Khi nào được gợi ý?", "Điều kiện eligibility", RED),
    ]
    for idx, (num, title, body, color) in enumerate(cards):
        x = 780_000 + idx * 3_020_000
        slide.shape(name=f"Question card {idx}", x=x, y=2_050_000, w=2_700_000, h=3_400_000, fill=CARD, line=LINE, prst="roundRect")
        slide.shape(name=f"Question chip {idx}", x=x + 260_000, y=2_360_000, w=590_000, h=460_000, fill=color, line=None, prst="roundRect")
        slide.text_box(
            name=f"Question num {idx}",
            x=x + 260_000,
            y=2_455_000,
            w=590_000,
            h=150_000,
            paragraphs=[{"text": num, "size": 950, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}],
        )
        slide.text_box(
            name=f"Question title {idx}",
            x=x + 260_000,
            y=3_080_000,
            w=2_130_000,
            h=720_000,
            paragraphs=[{"text": title, "size": 1780, "color": INK, "bold": True, "typeface": TYPE_TITLE, "space_after": 0}],
        )
        slide.text_box(
            name=f"Question body {idx}",
            x=x + 260_000,
            y=4_030_000,
            w=2_100_000,
            h=520_000,
            paragraphs=[{"text": body, "size": 1220, "color": MUTED, "space_after": 0}],
        )
        slide.shape(name=f"Question bottom {idx}", x=x + 260_000, y=4_920_000, w=1_260_000, h=70_000, fill=color, line=None, prst="roundRect")
    slide.shape(name="Bottom note", x=1_540_000, y=5_930_000, w=10_260_000, h=540_000, fill=MINT, line=None, prst="roundRect")
    slide.text_box(
        name="Bottom text",
        x=1_850_000,
        y=6_090_000,
        w=9_640_000,
        h=160_000,
        paragraphs=[{"text": "Nói ngắn gọn: catalog biến dữ liệu hành vi thành lựa chọn sản phẩm có kiểm soát.", "size": 1250, "color": GREEN_DARK, "bold": True, "align": "ctr", "space_after": 0}],
    )
    return slide


def catalog_map_slide(groups: list[dict[str, object]]) -> Slide:
    slide = Slide()
    slide.header("Catalog hiện có gì?", "Bản đồ danh mục")
    slide.text_box(
        name="Stat headline",
        x=780_000,
        y=1_200_000,
        w=4_600_000,
        h=1_100_000,
        paragraphs=[
            {"text": "15", "size": 5200, "color": GREEN, "bold": True, "typeface": TYPE_TITLE, "space_after": 0},
            {"text": "sản phẩm đang được recommendation sử dụng", "size": 1320, "color": MUTED, "space_after": 0},
        ],
    )
    slide.shape(name="Big total card", x=5_630_000, y=1_240_000, w=6_920_000, h=4_960_000, fill=CARD, line=LINE, prst="roundRect")
    max_count = max(int(group["count"]) for group in groups)
    colors = [GREEN, BLUE, AMBER, RED, "6D8A4E", "8B6B48", "5E7E72"]
    for idx, group in enumerate(groups):
        y = 1_600_000 + idx * 620_000
        bar_w = int(3_180_000 * int(group["count"]) / max_count)
        color = colors[idx % len(colors)]
        slide.text_box(
            name=f"Group label {idx}",
            x=6_000_000,
            y=y + 45_000,
            w=1_720_000,
            h=210_000,
            paragraphs=[{"text": str(group["label"]), "size": 1050, "color": INK, "bold": True, "space_after": 0}],
        )
        slide.shape(name=f"Bar bg {idx}", x=7_850_000, y=y + 95_000, w=3_300_000, h=130_000, fill=CREAM, line=None, prst="roundRect")
        slide.shape(name=f"Bar {idx}", x=7_850_000, y=y + 95_000, w=bar_w, h=130_000, fill=color, line=None, prst="roundRect")
        slide.text_box(
            name=f"Group count {idx}",
            x=11_280_000,
            y=y + 5_000,
            w=520_000,
            h=210_000,
            paragraphs=[{"text": str(group["count"]), "size": 1150, "color": color, "bold": True, "align": "ctr", "space_after": 0}],
        )
        slide.text_box(
            name=f"Examples {idx}",
            x=6_000_000,
            y=y + 285_000,
            w=5_700_000,
            h=180_000,
            paragraphs=[{"text": str(group["examples"]), "size": 830, "color": MUTED, "space_after": 0}],
        )
    slide.shape(name="Insight card", x=780_000, y=3_040_000, w=4_260_000, h=2_260_000, fill=INK, line=None, prst="roundRect")
    slide.text_box(
        name="Insight",
        x=1_080_000,
        y=3_410_000,
        w=3_660_000,
        h=1_450_000,
        paragraphs=[
            {"text": "Nhìn nhanh", "size": 1000, "color": "A7D7BF", "bold": True, "space_after": 0},
            {"text": "Insurance và Loan là hai nhóm lớn nhất.", "size": 1950, "color": "FFFFFF", "bold": True, "typeface": TYPE_TITLE, "space_after": 0},
            {"text": "Đây là nơi guardrail rủi ro cần phát huy rõ nhất.", "size": 1050, "color": "DDEBE2", "space_after": 0},
        ],
    )
    return slide


def behavior_bridge_slide() -> Slide:
    slide = Slide()
    slide.header("Vì sao cần catalog?", "Từ hành vi đến quyết định")
    slide.text_box(
        name="Caption",
        x=770_000,
        y=1_210_000,
        w=10_700_000,
        h=340_000,
        paragraphs=[{"text": "Nếu chỉ có hành vi khách hàng, hệ thống chưa biết nên gợi ý gì. Catalog là lớp dịch hành vi thành offer.", "size": 1370, "color": MUTED, "space_after": 0}],
    )
    pairs = [
        ("Mua sắm nhiều", "Cashback Card", GREEN),
        ("Du lịch thường xuyên", "Travel Insurance / Travel Card", BLUE),
        ("Áp lực dòng tiền", "Consumer / Overdraft Loan", AMBER),
        ("Rủi ro cao", "Không gợi ý sản phẩm rủi ro", RED),
    ]
    for idx, (behavior, product, color) in enumerate(pairs):
        y = 1_980_000 + idx * 1_080_000
        slide.shape(name=f"Behavior {idx}", x=850_000, y=y, w=3_600_000, h=690_000, fill=CARD, line=LINE, prst="roundRect")
        slide.text_box(name=f"Behavior text {idx}", x=1_100_000, y=y + 210_000, w=3_100_000, h=190_000, paragraphs=[{"text": behavior, "size": 1250, "color": INK, "bold": True, "space_after": 0}])
        slide.arrow(x=4_720_000, y=y + 210_000, w=1_130_000, h=230_000, color=color)
        slide.shape(name=f"Product {idx}", x=6_140_000, y=y, w=4_450_000, h=690_000, fill=color, line=None, prst="roundRect")
        slide.text_box(name=f"Product text {idx}", x=6_410_000, y=y + 205_000, w=3_900_000, h=200_000, paragraphs=[{"text": product, "size": 1210, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}])
        slide.shape(name=f"Rule {idx}", x=10_970_000, y=y + 125_000, w=640_000, h=430_000, fill=CREAM, line=None, prst="roundRect")
        slide.text_box(name=f"Rule text {idx}", x=10_970_000, y=y + 230_000, w=640_000, h=110_000, paragraphs=[{"text": "rule", "size": 830, "color": MUTED, "align": "ctr", "space_after": 0}])
    slide.shape(name="Main idea", x=1_480_000, y=6_200_000, w=10_360_000, h=450_000, fill=BLUE_LIGHT, line=None, prst="roundRect")
    slide.text_box(name="Main idea text", x=1_800_000, y=6_320_000, w=9_720_000, h=160_000, paragraphs=[{"text": "Catalog giúp recommendation có logic kinh doanh, không chỉ có model score.", "size": 1180, "color": BLUE, "bold": True, "align": "ctr", "space_after": 0}])
    return slide


def product_schema_slide() -> Slide:
    slide = Slide()
    slide.header("Mỗi sản phẩm gồm những gì?", "Schema dễ nhớ")
    fields = [
        ("product_id", "Mã sản phẩm", GREEN),
        ("product_name", "Tên hiển thị", GREEN),
        ("product_type", "Nhóm sản phẩm", BLUE),
        ("risk_allowed", "Mức rủi ro", RED),
        ("target_behavior", "Hành vi mục tiêu", AMBER),
        ("target_signals_json", "Feature để chấm điểm", BLUE),
        ("eligibility_json", "Điều kiện được phép gợi ý", RED),
        ("campaign_priority", "Ưu tiên chiến dịch", AMBER),
    ]
    slide.shape(name="Product object", x=4_780_000, y=1_720_000, w=3_760_000, h=3_860_000, fill=INK, line=None, prst="roundRect")
    slide.text_box(
        name="Object title",
        x=5_240_000,
        y=2_150_000,
        w=2_840_000,
        h=460_000,
        paragraphs=[{"text": "Product record", "size": 1900, "color": "FFFFFF", "bold": True, "typeface": TYPE_TITLE, "align": "ctr", "space_after": 0}],
    )
    slide.text_box(
        name="Object body",
        x=5_210_000,
        y=2_850_000,
        w=2_920_000,
        h=1_650_000,
        paragraphs=[
            {"text": "1 sản phẩm = dữ liệu + luật + tín hiệu", "size": 1250, "color": "DDEBE2", "align": "ctr", "space_after": 0},
            {"text": "Dùng để lọc, chấm điểm và giải thích.", "size": 1120, "color": "A7D7BF", "align": "ctr", "space_after": 0},
        ],
    )
    for idx, (field, meaning, color) in enumerate(fields):
        left = idx % 2 == 0
        row = idx // 2
        y = 1_480_000 + row * 1_190_000
        x = 720_000 if left else 8_960_000
        slide.shape(name=f"Field card {idx}", x=x, y=y, w=3_530_000, h=760_000, fill=CARD, line=LINE, prst="roundRect")
        slide.shape(name=f"Field accent {idx}", x=x, y=y, w=120_000, h=760_000, fill=color, line=None, prst="rect")
        slide.text_box(name=f"Field name {idx}", x=x + 300_000, y=y + 150_000, w=2_960_000, h=220_000, paragraphs=[{"text": field, "size": 1050, "color": color, "bold": True, "space_after": 0}])
        slide.text_box(name=f"Field meaning {idx}", x=x + 300_000, y=y + 420_000, w=2_960_000, h=180_000, paragraphs=[{"text": meaning, "size": 900, "color": MUTED, "space_after": 0}])
    return slide


def travel_example_slide(products: list[dict[str, object]]) -> Slide:
    travel = next(product for product in products if product["product_id"] == "P002")
    signals = travel["target_signals_json"]
    assert isinstance(signals, dict)
    eligibility = travel["eligibility_json"]
    assert isinstance(eligibility, dict)
    slide = Slide()
    slide.header("Ví dụ dễ hiểu: P002 Travel Insurance", "Một offer cụ thể")
    slide.shape(name="Main product card", x=760_000, y=1_350_000, w=4_100_000, h=4_990_000, fill=INK, line=None, prst="roundRect")
    slide.text_box(
        name="Product title",
        x=1_080_000,
        y=1_760_000,
        w=3_430_000,
        h=860_000,
        paragraphs=[
            {"text": "P002", "size": 1120, "color": "A7D7BF", "bold": True, "space_after": 0},
            {"text": str(travel["product_name"]), "size": 2450, "color": "FFFFFF", "bold": True, "typeface": TYPE_TITLE, "space_after": 0},
        ],
    )
    slide.shape(name="Low risk pill", x=1_080_000, y=2_910_000, w=1_500_000, h=430_000, fill=GREEN, line=None, prst="roundRect", text="risk: low", text_size=950, text_color="FFFFFF", bold=True)
    slide.text_box(
        name="Product desc",
        x=1_080_000,
        y=3_650_000,
        w=3_350_000,
        h=1_150_000,
        paragraphs=[
            {"text": "Phù hợp khi khách có tín hiệu chi tiêu du lịch gần đây và vẫn nằm trong ngưỡng rủi ro cho phép.", "size": 1260, "color": "F4F0E8", "space_after": 0}
        ],
    )
    slide.text_box(
        name="Reason",
        x=1_080_000,
        y=5_180_000,
        w=3_350_000,
        h=480_000,
        paragraphs=[{"text": str(travel["reason_template"]), "size": 960, "color": "DDEBE2", "space_after": 0}],
    )
    slide.shape(name="Signals panel", x=5_360_000, y=1_360_000, w=3_320_000, h=4_980_000, fill=CARD, line=LINE, prst="roundRect")
    slide.text_box(name="Signals title", x=5_700_000, y=1_730_000, w=2_600_000, h=320_000, paragraphs=[{"text": "Tín hiệu chấm điểm", "size": 1450, "color": INK, "bold": True, "typeface": TYPE_TITLE, "space_after": 0}])
    signal_labels = {
        "travel_ratio": "Travel ratio",
        "travel_frequency_90d": "Travel freq. 90d",
        "foreign_txn_proxy": "Foreign txn",
        "risk_score_inverse": "Risk inverse",
    }
    for idx, (key, weight) in enumerate(signals.items()):
        y = 2_260_000 + idx * 760_000
        bar_w = int(1_760_000 * float(weight) / 0.55)
        slide.text_box(name=f"Signal label {key}", x=5_720_000, y=y, w=2_210_000, h=180_000, paragraphs=[{"text": signal_labels.get(str(key), str(key)), "size": 880, "color": MUTED, "space_after": 0}])
        slide.shape(name=f"Signal bg {key}", x=5_720_000, y=y + 280_000, w=1_860_000, h=130_000, fill=CREAM, line=None, prst="roundRect")
        slide.shape(name=f"Signal bar {key}", x=5_720_000, y=y + 280_000, w=bar_w, h=130_000, fill=BLUE if idx < 2 else GREEN, line=None, prst="roundRect")
        slide.text_box(name=f"Signal weight {key}", x=7_690_000, y=y + 235_000, w=430_000, h=160_000, paragraphs=[{"text": f"{int(float(weight) * 100)}%", "size": 850, "color": INK, "bold": True, "align": "r", "space_after": 0}])
    slide.shape(name="Eligibility panel", x=9_080_000, y=1_360_000, w=3_460_000, h=4_980_000, fill=CARD, line=LINE, prst="roundRect")
    slide.text_box(name="Eligibility title", x=9_410_000, y=1_730_000, w=2_840_000, h=340_000, paragraphs=[{"text": "Điều kiện gợi ý", "size": 1450, "color": INK, "bold": True, "typeface": TYPE_TITLE, "space_after": 0}])
    slide.shape(name="Risk gate mini", x=9_520_000, y=2_400_000, w=2_500_000, h=1_220_000, fill=MINT, line=None, prst="roundRect")
    slide.text_box(name="Gate mini text", x=9_780_000, y=2_700_000, w=1_980_000, h=420_000, paragraphs=[{"text": f"max risk score ≤ {eligibility['max_risk_score']}", "size": 1300, "color": GREEN_DARK, "bold": True, "align": "ctr", "space_after": 0}])
    bullets = [
        "Có chi tiêu du lịch cao",
        "Có giao dịch liên quan du lịch trong 90 ngày",
        "Rủi ro thấp hoặc chỉ review nhẹ",
    ]
    slide.text_box(
        name="Eligibility bullets",
        x=9_500_000,
        y=4_050_000,
        w=2_720_000,
        h=1_200_000,
        paragraphs=[{"text": item, "size": 960, "color": MUTED, "bullet": True, "space_after": 300} for item in bullets],
    )
    return slide


def pipeline_slide() -> Slide:
    slide = Slide()
    slide.header("Cách hệ thống chọn sản phẩm", "Luồng recommendation")
    steps = [
        ("01", "User features", "Hành vi, frequency, amount, category"),
        ("02", "Risk gate", "Chặn fraud/risk trước"),
        ("03", "Eligibility", "Loại offer không đủ điều kiện"),
        ("04", "Scoring", "Tính điểm từng sản phẩm"),
        ("05", "Ranking", "Sắp xếp theo điểm"),
        ("06", "Top 3", "Trả về gợi ý tốt nhất"),
    ]
    colors = [BLUE, RED, AMBER, GREEN, BLUE, INK]
    for idx, (num, title, body) in enumerate(steps):
        x = 660_000 + idx * 2_070_000
        y = 2_250_000 if idx % 2 == 0 else 3_420_000
        slide.shape(name=f"Step {idx}", x=x, y=y, w=1_720_000, h=1_120_000, fill=CARD, line=LINE, prst="roundRect")
        slide.shape(name=f"Step badge {idx}", x=x + 190_000, y=y + 170_000, w=410_000, h=320_000, fill=colors[idx], line=None, prst="roundRect")
        slide.text_box(name=f"Step number {idx}", x=x + 190_000, y=y + 240_000, w=410_000, h=110_000, paragraphs=[{"text": num, "size": 730, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}])
        slide.text_box(name=f"Step title {idx}", x=x + 190_000, y=y + 570_000, w=1_330_000, h=190_000, paragraphs=[{"text": title, "size": 1010, "color": INK, "bold": True, "space_after": 0}])
        slide.text_box(name=f"Step body {idx}", x=x + 190_000, y=y + 810_000, w=1_330_000, h=200_000, paragraphs=[{"text": body, "size": 690, "color": MUTED, "space_after": 0}])
        if idx < len(steps) - 1:
            slide.arrow(x=x + 1_780_000, y=y + 480_000, w=470_000, h=170_000, color=colors[idx])
    slide.shape(name="Bottom insight", x=1_360_000, y=5_820_000, w=10_620_000, h=560_000, fill=INK, line=None, prst="roundRect")
    slide.text_box(name="Bottom insight text", x=1_720_000, y=6_000_000, w=9_900_000, h=160_000, paragraphs=[{"text": "Kết quả là chấm điểm từng khách hàng với từng sản phẩm, không gán cứng “một cụm = một sản phẩm”.", "size": 1150, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}])
    return slide


def score_formula_slide() -> Slide:
    slide = Slide()
    slide.header("Công thức điểm gợi ý", "5 thành phần")
    slide.shape(name="Center circle", x=5_155_000, y=2_290_000, w=3_050_000, h=3_050_000, fill=INK, line=None, prst="ellipse")
    slide.text_box(
        name="Center text",
        x=5_580_000,
        y=3_090_000,
        w=2_200_000,
        h=920_000,
        paragraphs=[
            {"text": "Product score", "size": 1180, "color": "A7D7BF", "bold": True, "align": "ctr", "space_after": 0},
            {"text": "Fit × Risk × Timing", "size": 1900, "color": "FFFFFF", "bold": True, "typeface": TYPE_TITLE, "align": "ctr", "space_after": 0},
        ],
    )
    components = [
        ("Behavior match", "Khớp hành vi khách", GREEN, 1_040_000, 1_620_000),
        ("Segment affinity", "Cụm khách hàng phù hợp", BLUE, 4_960_000, 1_070_000),
        ("Affordability fit", "Khả năng chi trả + rủi ro", AMBER, 8_940_000, 1_620_000),
        ("Timing need", "Nhu cầu gần đây", RED, 2_540_000, 5_330_000),
        ("Campaign priority", "Ưu tiên kinh doanh", "6D8A4E", 7_670_000, 5_330_000),
    ]
    for idx, (title, body, color, x, y) in enumerate(components):
        slide.shape(name=f"Component {idx}", x=x, y=y, w=2_440_000, h=940_000, fill=CARD, line=LINE, prst="roundRect")
        slide.shape(name=f"Component dot {idx}", x=x + 220_000, y=y + 220_000, w=210_000, h=210_000, fill=color, line=None, prst="ellipse")
        slide.text_box(name=f"Component title {idx}", x=x + 560_000, y=y + 200_000, w=1_680_000, h=200_000, paragraphs=[{"text": title, "size": 960, "color": INK, "bold": True, "space_after": 0}])
        slide.text_box(name=f"Component body {idx}", x=x + 560_000, y=y + 470_000, w=1_660_000, h=180_000, paragraphs=[{"text": body, "size": 760, "color": MUTED, "space_after": 0}])
        slide.line(x=x + 1_220_000, y=3_770_000 if y < 2_000_000 else 4_930_000, w=18_000, h=430_000, color=color, width=18_000)
    slide.shape(name="Formula note", x=2_020_000, y=6_490_000, w=9_300_000, h=420_000, fill=BLUE_LIGHT, line=None, prst="roundRect")
    slide.text_box(name="Formula note text", x=2_260_000, y=6_610_000, w=8_820_000, h=130_000, paragraphs=[{"text": "Mỗi thành phần giúp score vừa đúng dữ liệu, vừa đúng mục tiêu kinh doanh.", "size": 990, "color": BLUE, "bold": True, "align": "ctr", "space_after": 0}])
    return slide


def guardrail_slide() -> Slide:
    slide = Slide()
    slide.header("Guardrail rủi ro", "Fraud score là cổng chặn")
    lanes = [
        ("< 0.3", "Go", "Gợi ý đầy đủ sản phẩm đủ điều kiện", GREEN, MINT),
        ("0.3 - 0.7", "Review", "Chỉ giữ sản phẩm rủi ro thấp", AMBER, AMBER_LIGHT),
        (">= 0.7", "Stop", "Không gợi ý sản phẩm nào", RED, RED_LIGHT),
    ]
    for idx, (score, status, action, color, fill) in enumerate(lanes):
        x = 850_000 + idx * 4_100_000
        slide.shape(name=f"Guard card {idx}", x=x, y=1_780_000, w=3_520_000, h=3_920_000, fill=fill, line=None, prst="roundRect")
        slide.shape(name=f"Traffic light {idx}", x=x + 1_260_000, y=2_190_000, w=1_000_000, h=1_000_000, fill=color, line=None, prst="ellipse")
        slide.text_box(name=f"Score {idx}", x=x + 740_000, y=3_520_000, w=2_040_000, h=410_000, paragraphs=[{"text": score, "size": 2100, "color": color, "bold": True, "typeface": TYPE_TITLE, "align": "ctr", "space_after": 0}])
        slide.text_box(name=f"Status {idx}", x=x + 740_000, y=4_060_000, w=2_040_000, h=300_000, paragraphs=[{"text": status, "size": 1180, "color": INK, "bold": True, "align": "ctr", "space_after": 0}])
        slide.text_box(name=f"Action {idx}", x=x + 420_000, y=4_610_000, w=2_680_000, h=520_000, paragraphs=[{"text": action, "size": 990, "color": MUTED, "align": "ctr", "space_after": 0}])
    slide.shape(name="Why matters", x=1_580_000, y=6_170_000, w=10_120_000, h=490_000, fill=INK, line=None, prst="roundRect")
    slide.text_box(name="Why matters text", x=1_950_000, y=6_310_000, w=9_380_000, h=160_000, paragraphs=[{"text": "Guardrail giúp recommendation tăng doanh thu mà không tăng rủi ro vận hành.", "size": 1110, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}])
    return slide


def risk_mix_slide(risks: list[dict[str, object]]) -> Slide:
    slide = Slide()
    slide.header("Các nhóm sản phẩm theo rủi ro", "Risk mix")
    total = sum(int(risk["count"]) for risk in risks)
    colors = {"low": GREEN, "medium": AMBER, "high": RED}
    fills = {"low": MINT, "medium": AMBER_LIGHT, "high": RED_LIGHT}
    start_x = 1_040_000
    y = 2_060_000
    total_w = 11_250_000
    cursor = start_x
    for risk in risks:
        width = int(total_w * int(risk["count"]) / total)
        slide.shape(name=f"Stack {risk['risk']}", x=cursor, y=y, w=width, h=620_000, fill=colors[str(risk["risk"])], line=None, prst="rect")
        slide.text_box(name=f"Stack text {risk['risk']}", x=cursor, y=y + 180_000, w=width, h=160_000, paragraphs=[{"text": f"{risk['label']} · {risk['count']}", "size": 1040, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}])
        cursor += width
    detail = [
        ("low", "Low", "Dễ gợi ý, an toàn, phù hợp nhiều khách", "Bảo hiểm, tiết kiệm, bill payment"),
        ("medium", "Medium", "Cần kiểm tra điều kiện và risk score", "Thẻ tín dụng, khoản vay"),
        ("high", "High", "Chỉ dành cho khách phù hợp", "Investment fund"),
    ]
    for idx, (key, title, meaning, examples) in enumerate(detail):
        x = 1_040_000 + idx * 4_020_000
        slide.shape(name=f"Risk detail {key}", x=x, y=3_310_000, w=3_480_000, h=2_240_000, fill=fills[key], line=None, prst="roundRect")
        slide.shape(name=f"Risk dot {key}", x=x + 280_000, y=3_640_000, w=260_000, h=260_000, fill=colors[key], line=None, prst="ellipse")
        slide.text_box(name=f"Risk title {key}", x=x + 680_000, y=3_590_000, w=2_300_000, h=280_000, paragraphs=[{"text": title, "size": 1500, "color": colors[key], "bold": True, "typeface": TYPE_TITLE, "space_after": 0}])
        slide.text_box(name=f"Risk meaning {key}", x=x + 300_000, y=4_180_000, w=2_850_000, h=460_000, paragraphs=[{"text": meaning, "size": 940, "color": INK, "space_after": 0}])
        slide.text_box(name=f"Risk examples {key}", x=x + 300_000, y=4_890_000, w=2_850_000, h=280_000, paragraphs=[{"text": examples, "size": 830, "color": MUTED, "space_after": 0}])
    return slide


def update_catalog_slide() -> Slide:
    slide = Slide()
    slide.header("Cách cập nhật catalog", "Quy trình vận hành")
    steps = [
        ("01", "Cập nhật JSON", "configs/product_catalog.json", GREEN),
        ("02", "Kiểm tra target", "target_behavior + target_signals_json", BLUE),
        ("03", "Kiểm tra eligibility", "Điều kiện được phép gợi ý", RED),
        ("04", "Seed lại DB", "src.db.init_db --recreate", AMBER),
        ("05", "Kiểm tra dashboard", "Recommendation output", GREEN_DARK),
    ]
    for idx, (num, title, body, color) in enumerate(steps):
        y = 1_460_000 + idx * 950_000
        slide.shape(name=f"Update num {idx}", x=1_140_000, y=y, w=640_000, h=640_000, fill=color, line=None, prst="ellipse")
        slide.text_box(name=f"Update num text {idx}", x=1_140_000, y=y + 190_000, w=640_000, h=160_000, paragraphs=[{"text": num, "size": 930, "color": "FFFFFF", "bold": True, "align": "ctr", "space_after": 0}])
        if idx < len(steps) - 1:
            slide.shape(name=f"Connector {idx}", x=1_440_000, y=y + 655_000, w=42_000, h=310_000, fill=LINE, line=None, prst="rect")
        slide.shape(name=f"Update card {idx}", x=2_160_000, y=y, w=8_840_000, h=640_000, fill=CARD, line=LINE, prst="roundRect")
        slide.text_box(name=f"Update title {idx}", x=2_500_000, y=y + 145_000, w=3_000_000, h=180_000, paragraphs=[{"text": title, "size": 1110, "color": INK, "bold": True, "space_after": 0}])
        slide.text_box(name=f"Update body {idx}", x=5_700_000, y=y + 145_000, w=4_900_000, h=180_000, paragraphs=[{"text": body, "size": 910, "color": MUTED, "space_after": 0}])
    slide.shape(name="Command", x=2_160_000, y=6_390_000, w=8_840_000, h=420_000, fill=INK, line=None, prst="roundRect")
    slide.text_box(name="Command text", x=2_440_000, y=6_500_000, w=8_260_000, h=130_000, paragraphs=[{"text": r".\.venv\Scripts\python.exe -m src.db.init_db --db data\smart_finance.db --recreate", "size": 760, "color": "DDEBE2", "typeface": "Consolas", "align": "ctr", "space_after": 0}])
    return slide


def conclusion_slide() -> Slide:
    slide = Slide()
    slide.shape(name="Final bg", x=0, y=0, w=SLIDE_W, h=SLIDE_H, fill=INK, line=None, prst="rect")
    slide.shape(name="Final orb", x=8_000_000, y=900_000, w=4_500_000, h=4_500_000, fill=GREEN, line=None, prst="ellipse", alpha=35000)
    slide.text_box(
        name="Final title",
        x=1_040_000,
        y=1_220_000,
        w=7_800_000,
        h=1_330_000,
        paragraphs=[
            {"text": "Kết luận", "size": 4700, "color": "FFFFFF", "bold": True, "typeface": TYPE_TITLE, "space_after": 0},
            {"text": "Product Catalog là cầu nối giữa dữ liệu hành vi và quyết định gợi ý sản phẩm.", "size": 1480, "color": "DDEBE2", "space_after": 0},
        ],
    )
    outcomes = [
        ("Đúng sản phẩm", "Offer khớp hành vi và nhu cầu", GREEN),
        ("Giải thích rõ", "Có reason template và tín hiệu", BLUE),
        ("Tuân thủ rủi ro", "Fraud/risk policy đứng trước score", RED),
        ("Dễ mở rộng", "Thêm sản phẩm bằng cấu hình", AMBER),
    ]
    for idx, (title, body, color) in enumerate(outcomes):
        x = 1_040_000 + (idx % 2) * 5_430_000
        y = 3_320_000 + (idx // 2) * 1_330_000
        slide.shape(name=f"Outcome {idx}", x=x, y=y, w=4_930_000, h=940_000, fill="FFFDF8", line=None, prst="roundRect")
        slide.shape(name=f"Outcome marker {idx}", x=x + 260_000, y=y + 310_000, w=240_000, h=240_000, fill=color, line=None, prst="ellipse")
        slide.text_box(name=f"Outcome title {idx}", x=x + 680_000, y=y + 220_000, w=3_800_000, h=210_000, paragraphs=[{"text": title, "size": 1160, "color": INK, "bold": True, "space_after": 0}])
        slide.text_box(name=f"Outcome body {idx}", x=x + 680_000, y=y + 500_000, w=3_800_000, h=170_000, paragraphs=[{"text": body, "size": 850, "color": MUTED, "space_after": 0}])
    return slide


def build_slides(products: list[dict[str, object]]) -> list[Slide]:
    groups, risks = product_summary(products)
    return [
        cover_slide(products, groups, risks),
        four_questions_slide(),
        catalog_map_slide(groups),
        behavior_bridge_slide(),
        product_schema_slide(),
        travel_example_slide(products),
        pipeline_slide(),
        score_formula_slide(),
        guardrail_slide(),
        risk_mix_slide(risks),
        update_catalog_slide(),
        conclusion_slide(),
    ]


def presentation_xml(slide_count: int) -> str:
    slide_ids = "\n".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>' for i in range(slide_count))
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
    rels = [
        f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>'
        for i in range(slide_count)
    ]
    rels.append(
        f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{''.join(rels)}
</Relationships>"""


def slide_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
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
  <dc:title>Product Catalog Visual Deck</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>""",
        "docProps/app.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Visual PPTX Generator</Application>
  <PresentationFormat>Widescreen</PresentationFormat>
  <Slides>{slide_count}</Slides>
</Properties>""",
        "ppt/theme/theme1.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Product Catalog Visual">
  <a:themeElements>
    <a:clrScheme name="Finance">
      <a:dk1>{srgb(INK)}</a:dk1><a:lt1>{srgb(BG)}</a:lt1>
      <a:dk2>{srgb(MUTED)}</a:dk2><a:lt2>{srgb(CARD)}</a:lt2>
      <a:accent1>{srgb(GREEN)}</a:accent1><a:accent2>{srgb(AMBER)}</a:accent2>
      <a:accent3>{srgb(BLUE)}</a:accent3><a:accent4>{srgb(RED)}</a:accent4>
      <a:accent5>{srgb(GREEN_DARK)}</a:accent5><a:accent6>{srgb(CREAM)}</a:accent6>
      <a:hlink>{srgb(BLUE)}</a:hlink><a:folHlink>{srgb(RED)}</a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Finance"><a:majorFont><a:latin typeface="{TYPE_TITLE}"/></a:majorFont><a:minorFont><a:latin typeface="{TYPE_BODY}"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Finance">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
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


def write_pptx(catalog_path: Path, output_path: Path) -> None:
    products = load_catalog(catalog_path)
    slides = build_slides(products)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", content_types(len(slides)))
        package.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        package.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        for name, content in static_files(len(slides)).items():
            package.writestr(name, content)
        total = len(slides)
        for index, slide in enumerate(slides, start=1):
            package.writestr(f"ppt/slides/slide{index}.xml", slide.to_xml(index, total, footer=index not in {1, total}))
            package.writestr(f"ppt/slides/_rels/slide{index}.xml.rels", slide_rels())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a visual product catalog PPTX deck.")
    parser.add_argument("--catalog", type=Path, default=Path("configs/product_catalog.json"))
    parser.add_argument("--output", type=Path, default=Path("PRODUCT_CATALOG_VISUAL.pptx"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_pptx(args.catalog, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
