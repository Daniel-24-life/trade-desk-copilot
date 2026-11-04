"""
Offline Simulation Engine & Synthetic B2B Buyer Dataset
Provides 8 realistic B2B buyer inquiries across North America, Europe, and the Middle East,
enabling zero-API-key testing and offline demonstration.
"""

from typing import List, Dict, Any


MOCK_INQUIRIES: List[Dict[str, Any]] = [
    {
        "id": "scenario_01",
        "title": "Dubai Luxury Hotel Project (Architectural Downlights)",
        "buyer_name": "Tariq Mansoor",
        "company": "Al-Bahr Hospitality Engineering, Dubai",
        "app_hint": "WhatsApp",
        "message": "Hello, we are tendering a 5-star hotel project in Dubai. We need around 400 pcs of architectural recessed downlights with Cutout Ø95mm, deep anti-glare UGR<19, CRI>90, and DALI-2 dimming protocol. Can you provide IES files and CIF Dubai pricing?",
        "expected_product": "downlight",
        "expected_tier": "T1",
    },
    {
        "id": "scenario_02",
        "title": "US Amazon FBA Seller (Foldable Socket Fan Light)",
        "buyer_name": "David Miller",
        "company": "PrimeGlow Home Innovations LLC, California",
        "app_hint": "Alibaba TradeManager",
        "message": "Hi, I sell on Amazon US. Looking for your E26/E27 foldable socket fan light. We want to do a trial run of 300 pcs shipped to Amazon FBA warehouse in Los Angeles (ZIP 90001). Can you provide the master carton dimensions, total CBM, and can you paste our FNDSKU barcode labels?",
        "expected_product": "fan_light",
        "expected_tier": "T2",
    },
    {
        "id": "scenario_03",
        "title": "European Industrial LED Driver Sourcing",
        "buyer_name": "Klaus Schneider",
        "company": "Schneider LightTech GmbH, Munich",
        "app_hint": "Outlook",
        "message": "Dear Sales Team, We require 500 units of constant current flicker-free LED drivers for our architectural luminaire line. Needs selectable current 300-1050mA, TRIAC & 0-10V dimmable, PF>0.95, and CE/RoHS certified. Please share datasheet and FOB Shenzhen quotation.",
        "expected_product": "led_driver",
        "expected_tier": "T1",
    },
    {
        "id": "scenario_04",
        "title": "Urgent Evaluation Sample Order",
        "buyer_name": "Emily Watson",
        "company": "Studio Illuminare, London UK",
        "app_hint": "WhatsApp",
        "message": "Can you ship 2 samples of your 18W downlight to London via DHL express? We need to present them to the client next Tuesday. How much is the sample cost and freight?",
        "expected_product": "downlight",
        "expected_tier": "T2",
    },
    {
        "id": "scenario_05",
        "title": "Tough Price Objection & Competitor Bidding",
        "buyer_name": "Carlos Gomez",
        "company": "Iberica Lighting S.L., Madrid",
        "app_hint": "Alibaba TradeManager",
        "message": "Your quotation of $10.50 is too high for our local market. Another supplier from Zhongshan offered $8.50 with similar specs. Can you do $8.80 for 500 pcs? Otherwise we will have to go with them.",
        "expected_product": "downlight",
        "expected_tier": "T2",
    },
    {
        "id": "scenario_06",
        "title": "Low MOQ Trial Order Negotiation",
        "buyer_name": "Sarah Jenkins",
        "company": "Jenkins Lighting Boutique, Sydney",
        "app_hint": "WhatsApp",
        "message": "Your MOQ shows 100 pcs for the socket fan light, but this is a brand new product for our showroom. Can we start with 20 pcs as a test batch? If it sells well, we will order a 20ft container.",
        "expected_product": "fan_light",
        "expected_tier": "T2",
    },
    {
        "id": "scenario_07",
        "title": "Factory Verification & Full Audit Request",
        "buyer_name": "Jean-Pierre Laurent",
        "company": "Lumière Architecturales, Paris",
        "app_hint": "Outlook",
        "message": "Are you a direct manufacturing factory or a trading company? We require ISO 9001 certification, full CE/LVD and RoHS test reports, and an on-site video audit before placing orders. Please send credentials.",
        "expected_product": "general",
        "expected_tier": "T1",
    },
    {
        "id": "scenario_08",
        "title": "Multimodal Specification Match Inquiry",
        "buyer_name": "Ahmed Al-Farsi",
        "company": "Gulf Project Supplies, Riyadh",
        "app_hint": "WhatsApp",
        "message": "Looking for the exact match for 25W deep recessed COB spotlights, 24-degree beam angle with black baffle ring for a private villa in Riyadh. Quantity is 150 pcs.",
        "expected_product": "downlight",
        "expected_tier": "T1",
    },
]


def get_mock_scenario(scenario_id: str) -> Dict[str, Any]:
    for s in MOCK_INQUIRIES:
        if s["id"] == scenario_id:
            return s
    return MOCK_INQUIRIES[0]


def list_mock_scenarios() -> List[Dict[str, str]]:
    return [
        {"id": s["id"], "title": s["title"], "buyer": s["buyer_name"]}
        for s in MOCK_INQUIRIES
    ]
