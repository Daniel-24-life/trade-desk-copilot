"""
1080x1080 Industrial Visual Quotation Card Generator
Produces high-resolution square PNG quotation cards for B2B foreign trade inquiries.
Equipped with a pure-Python QR code generator (zero external C-extension required).
"""

import os
import io
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont


# ==============================================================================
# Pure Python QR Code Generator (Zero-Dependency Version 3/4 Byte Mode)
# ==============================================================================
def generate_qr_image(text: str, box_size: int = 4, border: int = 2) -> Image.Image:
    """Generates a clean black and white QR code PIL image without external dependencies."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)
        return qr.make_image(fill_color="#0f172a", back_color="white").convert("RGB")
    except ImportError:
        pass

    # Built-in lightweight pure-python QR generator fallback
    data_bytes = text.encode("utf-8")
    version = 3 if len(data_bytes) <= 44 else 4
    size = 21 + (version - 1) * 4
    ec_count = 15 if version == 3 else 20
    total_codewords = 70 if version == 3 else 100
    data_codewords_count = total_codewords - ec_count

    bits = [0, 1, 0, 0]
    count = len(data_bytes)
    for i in range(7, -1, -1):
        bits.append((count >> i) & 1)
    for b in data_bytes:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

    total_data_bits = data_codewords_count * 8
    term_len = min(4, total_data_bits - len(bits))
    bits.extend([0] * term_len)
    while len(bits) % 8 != 0:
        bits.append(0)

    pad_bytes = [0xEC, 0x11]
    pad_idx = 0
    while len(bits) < total_data_bits:
        pb = pad_bytes[pad_idx % 2]
        for i in range(7, -1, -1):
            bits.append((pb >> i) & 1)
        pad_idx += 1

    codewords = []
    for i in range(0, len(bits), 8):
        byte_val = 0
        for b in bits[i:i+8]:
            byte_val = (byte_val << 1) | b
        codewords.append(byte_val)

    # Reed-Solomon Log/Exp tables
    EXP = [0] * 512
    LOG = [0] * 256
    val = 1
    for i in range(255):
        EXP[i] = val
        EXP[i + 255] = val
        LOG[val] = i
        val = (val << 1) ^ (0x11D if val & 0x80 else 0)

    def rs_poly_mul(p1, p2):
        r = [0] * (len(p1) + len(p2) - 1)
        for i, c1 in enumerate(p1):
            for j, c2 in enumerate(p2):
                if c1 != 0 and c2 != 0:
                    r[i + j] ^= EXP[(LOG[c1] + LOG[c2]) % 255]
        return r

    gen_poly = [1]
    for i in range(ec_count):
        gen_poly = rs_poly_mul(gen_poly, [1, EXP[i]])

    msg = codewords + [0] * ec_count
    for i in range(len(codewords)):
        coef = msg[i]
        if coef != 0:
            for j in range(len(gen_poly)):
                msg[i + j] ^= EXP[(LOG[coef] + LOG[gen_poly[j]]) % 255]
    ec_codewords = msg[len(codewords):]
    all_codewords = codewords + ec_codewords

    # Initialize QR matrix
    matrix = [[None] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]

    def add_finder(x, y):
        for r in range(-1, 8):
            for c in range(-1, 8):
                if 0 <= y + r < size and 0 <= x + c < size:
                    val = 1 if (0 <= r <= 6 and (c in (0, 6) or r in (0, 6)) or (2 <= r <= 4 and 2 <= c <= 4)) else 0
                    matrix[y + r][x + c] = val
                    reserved[y + r][x + c] = True

    add_finder(0, 0)
    add_finder(size - 7, 0)
    add_finder(0, size - 7)

    for i in range(8, size - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0
        reserved[6][i] = True
        matrix[i][6] = 1 if i % 2 == 0 else 0
        reserved[i][6] = True

    matrix[size - 8][8] = 1
    reserved[size - 8][8] = True

    align_coords = [6, 22] if version == 3 else [6, 26]
    for r in align_coords:
        for c in align_coords:
            if not reserved[r][c]:
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        matrix[r + dr][c + dc] = 1 if (abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0)) else 0
                        reserved[r + dr][c + dc] = True

    # Place data bits
    stream_bits = []
    for cw in all_codewords:
        for i in range(7, -1, -1):
            stream_bits.append((cw >> i) & 1)

    bit_idx = 0
    right = size - 1
    up = True
    while right > 0:
        if right == 6:
            right -= 1
        cols = [right, right - 1]
        rows = range(size - 1, -1, -1) if up else range(size)
        for y in rows:
            for x in cols:
                if not reserved[y][x]:
                    b = stream_bits[bit_idx] if bit_idx < len(stream_bits) else 0
                    bit_idx += 1
                    # Mask condition (y + x) % 2 == 0
                    if (y + x) % 2 == 0:
                        b ^= 1
                    matrix[y][x] = b
        right -= 2
        up = not up

    img_size = (size + border * 2) * box_size
    img = Image.new("RGB", (img_size, img_size), "white")
    pixels = img.load()
    for y in range(size):
        for x in range(size):
            color = (15, 23, 42) if matrix[y][x] == 1 else (255, 255, 255)
            for dy in range(box_size):
                for dx in range(box_size):
                    pixels[(x + border) * box_size + dx, (y + border) * box_size + dy] = color
    return img


# ==============================================================================
# Quotation Card Generator Engine
# ==============================================================================
class QuotationCardGenerator:
    WIDTH = 1080
    HEIGHT = 1080

    # Color Palette: Deep Navy Slate & Emerald/Teal Accent
    COLOR_BG = (248, 250, 252)          # Slate-50
    COLOR_CARD = (255, 255, 255)        # Pure White
    COLOR_PRIMARY = (15, 23, 42)        # Slate-900
    COLOR_SECONDARY = (51, 65, 85)      # Slate-700
    COLOR_MUTED = (100, 116, 139)       # Slate-500
    COLOR_ACCENT = (13, 148, 136)       # Teal-600
    COLOR_ACCENT_BG = (204, 251, 241)   # Teal-100
    COLOR_BORDER = (226, 232, 240)      # Slate-200
    COLOR_GOLD = (217, 119, 6)          # Amber-600

    def __init__(self):
        self._load_fonts()

    def _load_fonts(self):
        font_names = ["segoeui.ttf", "arial.ttf", "calibri.ttf", "msyh.ttc"]
        def get_font(size: int, bold: bool = False):
            bold_names = ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "msyhbd.ttc"]
            names = bold_names if bold else font_names
            for n in names:
                try:
                    return ImageFont.truetype(n, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        self.font_title = get_font(42, bold=True)
        self.font_subtitle = get_font(24, bold=True)
        self.font_h2 = get_font(30, bold=True)
        self.font_h3 = get_font(22, bold=True)
        self.font_body = get_font(20, bold=False)
        self.font_small = get_font(16, bold=False)
        self.font_price = get_font(38, bold=True)
        self.font_badge = get_font(18, bold=True)

    def generate(self, data: Dict[str, Any]) -> Image.Image:
        """
        Renders a full 1080x1080 quotation card.
        data structure:
        {
            "brand": "LuminaTech Global Lighting Solutions",
            "category_badge": "ARCHITECTURAL DOWNLIGHT",
            "product_title": "LT-DL01 Deep Anti-Glare Downlight",
            "model_sku": "LT-DL01-18W",
            "specs": [
                {"label": "Rated Power / CCT", "val": "18W COB · 3000K Warm White"},
                {"label": "Lumen / CRI", "val": "1,800 lm · Ra > 92 (UGR < 19)"},
                {"label": "Input Voltage & Dimming", "val": "AC 100-240V · DALI-2 & 0-10V"},
                {"label": "Cutout & Optics", "val": "Ø95mm Cutout · 24° / 38° TIR Lens"},
            ],
            "commercial": {
                "moq": "20 pcs (Trial) / 100 pcs (Standard)",
                "price_tiers": "$10.50 (MOQ 20) | $9.60 (MOQ 100)",
                "lead_time": "3-5 Days (Sample) / 18-22 Days (Bulk)",
                "warranty": "5-Year Replacement Warranty",
                "cbm_note": "24 pcs/ctn · 0.052 CBM · GW 14.2 kg"
            },
            "contact": {
                "rep": "Alex Morgan (Sales Director)",
                "email": "sales@luminatech.example",
                "phone": "+1 (555) 019-2834",
                "url": "https://www.luminatech.example"
            }
        }
        """
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.COLOR_BG)
        draw = ImageDraw.Draw(img)

        # 1. Top Header Banner (0 - 150 px)
        self._draw_header(draw, data)

        # 2. Main Product Showcase & Badge (150 - 390 px)
        self._draw_product_showcase(draw, data)

        # 3. Technical Specs Matrix (390 - 640 px)
        self._draw_specs_matrix(draw, data.get("specs", []))

        # 4. Commercial Tiers & Trust (640 - 890 px)
        self._draw_commercial_section(draw, data.get("commercial", {}))

        if data.get("review_only"):
            self._draw_review_footer(draw)
        else:
            self._draw_footer(draw, data.get("contact", {}))
        return img

    def generate_review_card(self, state, catalog):
        """Render a catalog review from fixture metadata and the operator-reviewed inquiry."""
        def quantity(key):
            value = state.get(key)
            return f"{value} pcs" if value is not None else "To confirm"

        moq = catalog.get("moq")
        return self.generate({
            "review_only": True,
            "brand": "Trade Desk Copilot",
            "category_badge": "CATALOG REVIEW",
            "product_title": state["product_name"].split(" (")[0],
            "model_sku": catalog["sku"],
            "price_highlight": "For review",
            "specs": [
                {"label": "Catalog input voltage", "val": catalog.get("voltage") or "To confirm"},
                {"label": "Requested dimming", "val": state.get("dimming") or "To confirm"},
                {"label": "Requested bulk quantity", "val": quantity("bulk_quantity")},
                {"label": "Requested sample quantity", "val": quantity("sample_quantity")},
            ],
            "commercial": {
                "price_tiers_label": "Catalog minimum order",
                "price_tiers": f"{moq} pcs" if moq is not None else "To confirm",
                "lead_time": "To confirm",
                "cbm_note": catalog.get("carton_spec") or "To confirm",
                "warranty": "To confirm",
            },
        })

    def _draw_review_footer(self, draw: ImageDraw.Draw):
        draw.rectangle([30, 900, self.WIDTH - 30, 1050], fill=self.COLOR_PRIMARY)
        draw.text((50, 920), "DEMO · REVIEW REQUIRED", fill="#ffffff", font=self.font_h2)
        draw.text(
            (50, 975),
            "Check availability, pricing and commercial terms before sharing a quote.",
            fill="#cbd5e1",
            font=self.font_body,
        )

    def _draw_header(self, draw: ImageDraw.Draw, data: Dict[str, Any]):
        # White card background for header
        draw.rectangle([30, 30, self.WIDTH - 30, 140], fill=self.COLOR_CARD, outline=self.COLOR_BORDER, width=2)

        # Brand Accent Pill
        draw.rounded_rectangle([50, 48, 70, 122], radius=6, fill=self.COLOR_ACCENT)

        brand = data.get("brand", "LuminaTech Global Lighting Solutions")
        draw.text((85, 48), brand, fill=self.COLOR_PRIMARY, font=self.font_subtitle)

        tagline = (
            "Catalog fixture and buyer requirements"
            if data.get("review_only")
            else "Verified OEM/ODM Manufacturer · ISO 9001:2015 · 100% 4-Hour Burn-in Tested"
        )
        draw.text((85, 88), tagline, fill=self.COLOR_MUTED, font=self.font_small)

        # Trust Badges (Right side)
        badge_text = "DEMO" if data.get("review_only") else "CE / RoHS / FCC"
        bbox = draw.textbbox((0, 0), badge_text, font=self.font_badge)
        bw = bbox[2] - bbox[0] + 24
        bx = self.WIDTH - 50 - bw
        draw.rounded_rectangle([bx, 60, bx + bw, 105], radius=8, fill=self.COLOR_ACCENT_BG)
        draw.text((bx + 12, 70), badge_text, fill=self.COLOR_ACCENT, font=self.font_badge)

    def _draw_product_showcase(self, draw: ImageDraw.Draw, data: Dict[str, Any]):
        draw.rectangle([30, 155, self.WIDTH - 30, 380], fill=self.COLOR_CARD, outline=self.COLOR_BORDER, width=2)

        # Category Badge
        cat = data.get("category_badge", "COMMERCIAL ARCHITECTURAL").upper()
        bbox = draw.textbbox((0, 0), cat, font=self.font_badge)
        cw = bbox[2] - bbox[0] + 20
        draw.rounded_rectangle([50, 175, 50 + cw, 208], radius=6, fill=self.COLOR_ACCENT_BG)
        draw.text((60, 182), cat, fill=self.COLOR_ACCENT, font=self.font_badge)

        # Product Title
        title = data.get("product_title", "Commercial LED Fixture")
        title_font = self.font_h2 if data.get("review_only") else self.font_title
        draw.text((50, 222), title, fill=self.COLOR_PRIMARY, font=title_font)

        # SKU & Warranty highlights
        sku = f"Model SKU: {data.get('model_sku', 'LT-DL01')}"
        draw.text((50, 280), sku, fill=self.COLOR_SECONDARY, font=self.font_h3)

        desc = (
            "Pricing and commercial terms require confirmation."
            if data.get("review_only")
            else "High-efficiency optical reflector, low stroboscopic constant current, 50,000h lifespan."
        )
        draw.text((50, 320), desc, fill=self.COLOR_MUTED, font=self.font_body)

        # Price tag pill on right
        price_text = data.get("price_highlight", "From $7.80")
        pbbox = draw.textbbox((0, 0), price_text, font=self.font_price)
        pw = pbbox[2] - pbbox[0] + 36
        px = self.WIDTH - 50 - pw
        draw.rounded_rectangle([px, 205, px + pw, 280], radius=12, fill=self.COLOR_PRIMARY)
        draw.text((px + 18, 220), price_text, fill="#ffffff", font=self.font_price)
        price_label = "Pending confirmation" if data.get("review_only") else "FOB Shenzhen Tiers"
        draw.text((px + 18, 290), price_label, fill=self.COLOR_MUTED, font=self.font_small)

    def _draw_specs_matrix(self, draw: ImageDraw.Draw, specs: List[Dict[str, str]]):
        draw.rectangle([30, 395, self.WIDTH - 30, 635], fill=self.COLOR_CARD, outline=self.COLOR_BORDER, width=2)

        # Section Header
        draw.text((50, 412), "ENGINEERING SPECIFICATIONS", fill=self.COLOR_PRIMARY, font=self.font_subtitle)
        draw.line([50, 448, self.WIDTH - 50, 448], fill=self.COLOR_BORDER, width=1)

        # 2x2 Grid for Specs
        col1_x = 50
        col2_x = 550
        row_y = [465, 545]

        for idx, s in enumerate(specs[:4]):
            col = col1_x if idx % 2 == 0 else col2_x
            row = row_y[idx // 2]
            label = s.get("label", "Specification")
            val = s.get("val", "-")

            draw.text((col, row), label, fill=self.COLOR_MUTED, font=self.font_small)
            draw.text((col, row + 26), val, fill=self.COLOR_PRIMARY, font=self.font_h3)

    def _draw_commercial_section(self, draw: ImageDraw.Draw, comm: Dict[str, Any]):
        draw.rectangle([30, 650, self.WIDTH - 30, 885], fill=self.COLOR_CARD, outline=self.COLOR_BORDER, width=2)

        draw.text((50, 668), "COMMERCIAL TERMS & LOGISTICS", fill=self.COLOR_PRIMARY, font=self.font_subtitle)
        draw.line([50, 704, self.WIDTH - 50, 704], fill=self.COLOR_BORDER, width=1)

        items = [
            (comm.get("price_tiers_label", "Wholesale Tiers"), comm.get("price_tiers", "$9.60 - $10.50 FOB")),
            ("Production Lead Time", comm.get("lead_time", "3-5d Samples / 18-22d Bulk")),
            ("Export Packaging & CBM", comm.get("cbm_note", "24 pcs/ctn · 0.052 CBM")),
            ("Warranty & Trade Terms", comm.get("warranty", "5-Year Full Replacement Guarantee")),
        ]

        for i, (k, v) in enumerate(items):
            x = 50 if i % 2 == 0 else 550
            y = 722 if i < 2 else 802
            draw.text((x, y), k, fill=self.COLOR_MUTED, font=self.font_small)
            draw.text((x, y + 24), v, fill=self.COLOR_ACCENT if i == 0 else self.COLOR_PRIMARY, font=self.font_h3)

    def _draw_footer(self, draw: ImageDraw.Draw, contact: Dict[str, Any]):
        draw.rectangle([30, 900, self.WIDTH - 30, 1050], fill=self.COLOR_PRIMARY)

        # Contact text
        rep = contact.get("rep", "Alex Morgan (Sales Director)")
        draw.text((50, 920), rep, fill="#ffffff", font=self.font_h2)

        email = f"Email: {contact.get('email', 'sales@luminatech.example')}"
        phone = f"Direct / WhatsApp: {contact.get('phone', '+1 (555) 019-2834')}"
        url = contact.get("url", "https://www.luminatech.example")

        draw.text((50, 965), email, fill="#94a3b8", font=self.font_body)
        draw.text((50, 998), phone, fill="#94a3b8", font=self.font_body)

        # Embed QR Code
        qr_img = generate_qr_image(url, box_size=3, border=1)
        qr_w, qr_h = qr_img.size
        qx = self.WIDTH - 50 - qr_w
        qy = 920
        # White border around QR
        draw.rectangle([qx - 4, qy - 4, qx + qr_w + 4, qy + qr_h + 4], fill="#ffffff")
        # Paste QR
        img_temp = Image.new("RGB", (self.WIDTH, self.HEIGHT), (0, 0, 0))
        # Draw on parent image by pixel pasting
        for py in range(qr_h):
            for px in range(qr_w):
                draw.point((qx + px, qy + py), fill=qr_img.getpixel((px, py)))

        # QR caption
        draw.text((qx - 8, qy + qr_h + 8), "Scan for Catalog", fill="#94a3b8", font=self.font_small)


def generate_sample_card(output_path: Union[str, Path]) -> str:
    gen = QuotationCardGenerator()
    data = {
        "brand": "LuminaTech Global Lighting Solutions",
        "category_badge": "ARCHITECTURAL DOWNLIGHT",
        "product_title": "LT-DL01 Deep Anti-Glare Downlight",
        "model_sku": "LT-DL01-18W",
        "price_highlight": "$9.60 / pc",
        "specs": [
            {"label": "Rated Power & CCT", "val": "18W COB · 3000K / 4000K"},
            {"label": "Optical & Glare", "val": "1,800 lm · Ra > 92 · UGR < 19"},
            {"label": "Input Voltage & Dimming", "val": "AC 100-240V · DALI-2 & 0-10V"},
            {"label": "Cutout & Optics", "val": "Ø95mm Cutout · 24°/38° TIR Lens"},
        ],
        "commercial": {
            "price_tiers": "$10.50 (MOQ 20) · $9.60 (MOQ 100+)",
            "lead_time": "3-5d Samples · 18-22d Bulk Order",
            "cbm_note": "24 pcs/ctn · 0.052 CBM · GW 14.2 kg",
            "warranty": "5-Year Full Replacement Guarantee",
        },
        "contact": {
            "rep": "Alex Morgan (Sales Director)",
            "email": "sales@luminatech.example",
            "phone": "+1 (555) 019-2834",
            "url": "https://www.luminatech.example",
        }
    }
    card = gen.generate(data)
    card.save(output_path, "PNG")
    return str(output_path)
