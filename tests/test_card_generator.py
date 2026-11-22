import os
from pathlib import Path
from core.card_generator import QuotationCardGenerator, generate_qr_image, generate_sample_card


def test_pure_python_qr():
    qr = generate_qr_image("https://www.luminatech.example")
    assert qr is not None
    assert qr.size[0] > 50
    assert qr.size[1] > 50


def test_card_generator():
    gen = QuotationCardGenerator()
    data = {
        "brand": "LuminaTech Global Lighting Solutions",
        "category_badge": "ARCHITECTURAL DOWNLIGHT",
        "product_title": "LT-DL01 Anti-Glare Downlight",
        "model_sku": "LT-DL01-18W",
        "price_highlight": "From $7.80",
        "specs": [
            {"label": "Rated Power / CCT", "val": "18W · 3000K / 4000K"},
            {"label": "Lumen / CRI", "val": "1,800 lm · Ra > 92 (UGR < 19)"},
            {"label": "Input Voltage & Dimming", "val": "AC 100-240V · DALI-2 & 0-10V"},
            {"label": "Cutout & Optics", "val": "Ø95mm Cutout · 24°/38° TIR Lens"},
        ],
        "commercial": {
            "price_tiers": "$10.50 (MOQ 20) | $9.60 (MOQ 100)",
            "lead_time": "3-5 Days (Sample) / 18-22 Days (Bulk)",
            "warranty": "5-Year Replacement Warranty",
            "cbm_note": "24 pcs/ctn · 0.052 CBM · GW 14.2 kg"
        },
        "contact": {
            "rep": "Alex Morgan",
            "email": "sales@luminatech.example",
            "phone": "+1 (555) 019-2834",
            "url": "https://www.luminatech.example"
        }
    }
    img = gen.generate(data)
    assert img.size == (1080, 1080)

    out_file = Path(__file__).resolve().parent / "_test_card_out.png"
    try:
        img.save(out_file)
        assert out_file.exists()
        assert out_file.stat().st_size > 10000
    finally:
        if out_file.exists():
            out_file.unlink()
