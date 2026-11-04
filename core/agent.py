"""
Trade Desk Copilot - Core Agent & Multi-Style Negotiation Engine
Orchestrates buyer intent classification, RAG product parameter injection,
multi-turn dialogue state tracking (DST), and multi-style response synthesis.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from core.loader import CorpusLoader
from core.retriever import HybridRetriever
from core.dst import DialogueStateTracker, DialogueState
from core.clipboard_cleaner import format_for_target_app

STYLE_GOLD_NEGOTIATION = "gold_negotiation"   # 🌟 Balanced B2B Deal-Closing (Default)
STYLE_WHATSAPP_CONCISE = "whatsapp_concise"   # ⚡ Ultra-Concise IM Style
STYLE_ENGINEERING_SPEC = "engineering_spec"   # 📐 Technical Engineering Spec

STYLE_NAMES = {
    STYLE_GOLD_NEGOTIATION: "🌟 Gold B2B Closing",
    STYLE_WHATSAPP_CONCISE: "⚡ WhatsApp Concise",
    STYLE_ENGINEERING_SPEC: "📐 Engineering Spec",
}


def format_salutation(buyer_name: Optional[str], style: str = STYLE_GOLD_NEGOTIATION) -> str:
    """Produces clean professional English greetings without erroneous 'Dear there' concatenation."""
    is_valid_name = bool(
        buyer_name
        and buyer_name.strip()
        and buyer_name.strip().lower() not in ("friend", "there", "buyer", "customer", "sir", "madam", "unknown", "none")
    )
    clean_name = buyer_name.strip() if is_valid_name else ""

    if style == STYLE_ENGINEERING_SPEC:
        return f"Dear {clean_name}," if clean_name else "Dear Partner,"
    elif style == STYLE_WHATSAPP_CONCISE:
        return f"Hi {clean_name}," if clean_name else "Hi there,"
    else:
        return f"Hi {clean_name}," if clean_name else "Hello,"


class TradeDeskAgent:
    def __init__(self, loader: Optional[CorpusLoader] = None):
        self.loader = loader or CorpusLoader()
        self.retriever = HybridRetriever(self.loader)
        self.dst = DialogueStateTracker()

    def analyze_buyer_intent(self, message: str) -> Dict[str, Any]:
        """Classifies buyer tier and detects negotiation scenarios."""
        msg_lower = message.lower()

        t1_keywords = ["hotel", "project", "tender", "ies", "dialux", "contractor", "architect", "0-10v", "dali", "ugr", "cri92", "hospitality", "villa"]
        t2_keywords = ["amazon", "fba", "dropship", "trial order", "sample", "carton", "cbm", "barcode", "gift box", "distributor", "wholesale"]
        
        is_price_objection = any(w in msg_lower for w in ["expensive", "too high", "lower price", "competitor", "discount", "budget", "cheaper", "better price", "target price"])
        is_sample_request = any(w in msg_lower for w in ["sample", "test 1", "test 2", "freight", "dhl", "courier", "shipping cost"])
        is_moq_objection = any(w in msg_lower for w in ["moq is too high", "lower moq", "10 pcs", "20 pcs", "small quantity", "mixed order", "trial order"])
        is_factory_audit = any(w in msg_lower for w in ["factory or trading", "certificate", "ce cert", "rohs", "audit", "visit", "video call", "factory tour"])

        t1_score = sum(1 for w in t1_keywords if w in msg_lower)
        t2_score = sum(1 for w in t2_keywords if w in msg_lower)

        if t1_score >= 1 or any(w in msg_lower for w in ["ies", "hotel", "project", "0-10v", "dali"]):
            tier = "Tier 1: High-Value Architectural & Project OEM"
            tier_code = "T1"
        elif t2_score >= 1 or is_sample_request or is_moq_objection:
            tier = "Tier 2: E-Commerce / Amazon FBA / Regional Distributor"
            tier_code = "T2"
        else:
            tier = "Tier 3: General Inquiries & Price Screening"
            tier_code = "T3"

        scenarios = []
        if is_price_objection: scenarios.append("Price Objection")
        if is_sample_request: scenarios.append("Sample & Freight Request")
        if is_moq_objection: scenarios.append("MOQ Negotiation")
        if is_factory_audit: scenarios.append("Factory Verification & Certifications")
        if not scenarios: scenarios.append("General Product Inquiry")

        return {
            "tier": tier,
            "tier_code": tier_code,
            "scenarios": scenarios,
            "is_price_objection": is_price_objection,
            "is_sample_request": is_sample_request,
            "is_moq_objection": is_moq_objection,
            "is_factory_audit": is_factory_audit,
        }

    def process_inquiry(
        self,
        buyer_message: str,
        session_id: str = "default",
        buyer_name: Optional[str] = None,
        style: str = STYLE_GOLD_NEGOTIATION,
        target_app: str = "general"
    ) -> Dict[str, Any]:
        """End-to-end inquiry processing: intent -> DST update -> RAG retrieval -> synthesis."""
        intent = self.analyze_buyer_intent(buyer_message)
        state = self.dst.update_from_buyer_message(session_id, buyer_message, intent)

        # Retrieval query enrichment from DST slots
        query_parts = [buyer_message]
        if state.product_name:
            query_parts.append(state.product_name)
        if state.dimming:
            query_parts.append(state.dimming)
        enriched_query = " ".join(query_parts)

        matched_chunks = self.retriever.retrieve(enriched_query, top_k=3)
        english_reply, chinese_summary = self._synthesize_response(
            message=buyer_message,
            intent=intent,
            state=state,
            matched_chunks=matched_chunks,
            buyer_name=buyer_name,
            style=style
        )

        formatted = format_for_target_app(english_reply, app_hint=target_app)

        return {
            "session_id": session_id,
            "intent": intent,
            "state": state.to_dict(),
            "matched_references": matched_chunks,
            "english_reply": english_reply,
            "chinese_summary": chinese_summary,
            "formatted": formatted,
            "style": style,
        }

    def _synthesize_response(
        self,
        message: str,
        intent: Dict[str, Any],
        state: DialogueState,
        matched_chunks: List[Dict[str, Any]],
        buyer_name: Optional[str],
        style: str
    ) -> Tuple[str, str]:
        salutation = format_salutation(buyer_name, style)

        # 1. Product Knowledge Grounding
        product_title = "our architectural lighting line"
        sku = "standard catalog specification"
        moq_val = "20 pcs"
        cbm_val = "standard export carton"
        price_tier = "$7.80 - $12.50 FOB"

        if matched_chunks:
            top = matched_chunks[0]
            product_title = top["title"]
            sku = top.get("sku") or sku
            moq_val = f"{top.get('moq')} pcs" if top.get("moq") else moq_val
            cbm_val = str(top.get("cbm")) if top.get("cbm") else cbm_val

        # 2. Synthesis based on Style and Scenarios
        if style == STYLE_WHATSAPP_CONCISE:
            # WhatsApp short punchy style
            lines = [salutation]
            if intent.get("is_sample_request"):
                lines.append(f"Yes, samples of **{product_title}** are ready in stock!")
                lines.append("Testing 1–2 units takes 48h to ship via DHL/FedEx.")
                if state.destination_zip:
                    lines.append(f"Courier shipping to **{state.destination_zip}** takes ~4-5 working days.")
                lines.append("Shall I draft a quick Trade Assurance sample link for you?")
            elif intent.get("is_price_objection"):
                lines.append("Got your budget point. We use pure ADC12 aluminum and Bridgelux COB.")
                if state.quantity and state.quantity >= 100:
                    lines.append(f"For **{state.quantity} pcs**, we can lock **$9.60 FOB** with free laser logo engraving.")
                else:
                    lines.append("Let's do a 20-unit trial order at bulk pricing so you can inspect quality on-site.")
                lines.append("Would this meet your timeline?")
            else:
                lines.append(f"Thanks for reaching out! Regarding **{product_title}**:")
                lines.append(f"• MOQ: **{moq_val}** | Packaging: **{cbm_val}**")
                lines.append("• Full CE/RoHS compliance & 5-year replacement warranty.")
                lines.append("Are you sourcing for an ongoing project or wholesale distribution?")
            eng = "\n\n".join(lines)
            zh = f"WhatsApp极简回复：确认品类 ({product_title})，突出交期与核心条款，引导下单样品或试单。"

        elif style == STYLE_ENGINEERING_SPEC:
            # Technical specification style
            lines = [salutation]
            lines.append(f"Thank you for your technical inquiry regarding **{product_title}** ({sku}). Below is our official engineering overview:")
            lines.append(
                "**1. Optical & Electrical Specs**:\n"
                f"• Voltage Range: **{state.voltage or 'AC 100-240V (50/60Hz)'}**\n"
                f"• Dimming Protocol: **{state.dimming or 'DALI-2 / 0-10V / Non-dimming selectable'}**\n"
                "• Unified Glare Rating: **UGR < 19** with interchangeable secondary reflector\n"
                "• Color Rendering: **CRI Ra > 92** (MacAdam 3-step ellipse, R9 > 50)"
            )
            lines.append(
                "**2. Packaging & Logistics Breakdown**:\n"
                f"• Carton Specification: **{cbm_val}**\n"
                f"• Production Lead Time: **3–5 business days for evaluation samples; 18–22 days for bulk**\n"
                "• Quality Backing: **100% 4-Hour full-load burn-in tested; ISO 9001:2015 & CE/RoHS compliant**"
            )
            lines.append("Complete IES photometric files and DIALux simulation curves are available upon request. Would you like me to send over the specification sheet?")
            eng = "\n\n".join(lines)
            zh = f"工程技术详单：列出电气与光学参数 (UGR<19, CRI>92)、箱规 CBM 与 5年质保背书，提供 IES/DIALux 支持。"

        else:
            # Gold Negotiation (Default B2B closing)
            lines = [salutation]
            lines.append(f"Thank you for contacting **LuminaTech Global Solutions**. We are pleased to assist you with our **{product_title}**.")

            if intent.get("is_sample_request"):
                lines.append(
                    "We fully support evaluation samples so your team can test the optical performance and build quality first-hand. "
                    "Sample units are dispatched within **48 hours**, and sample costs are **100% refundable** upon confirming a formal order."
                )
            elif intent.get("is_price_objection"):
                lines.append(
                    "We understand target price considerations for competitive bidding. Our fixtures are manufactured with high-thermal cold-forged heatsinks and certified flicker-free drivers (50,000h lifespan). "
                    f"To support your initial run, we can offer our top-tier tier price (**$9.60 FOB**) for a test batch of **{state.quantity or '100'} pcs**."
                )
            else:
                lines.append(
                    f"For your initial review, our standard MOQ is **{moq_val}**, with production completed in **18–22 days**. "
                    f"Master export cartons are packed at **{cbm_val}**, optimized for sea freight and pallet stability."
                )

            lines.append(
                "All shipments are protected by **Alibaba Trade Assurance** (30% deposit, 70% before delivery against QC inspection photos) and backed by our **5-Year Full Replacement Guarantee**.\n\n"
                "Please let us know your planned quantity or destination port, and we will prepare a formal commercial proforma invoice."
            )
            eng = "\n\n".join(lines)
            zh = f"金牌谈判博弈：兼顾商业条款、信保定金保障与5年质保，促成初次试单并锁定下一步商务行动。"

        return eng, zh

    def refine_response(self, current_text: str, refinement_instruction: str) -> str:
        """Inline prompt refinement allowing operators to adjust pricing, terms, or brevity on the fly."""
        instr_lower = refinement_instruction.lower()
        refined = current_text

        # 1. Brevity / Shorten
        if any(w in instr_lower for w in ["精简", "shorten", "concise", "brief", "50%"]):
            paragraphs = [p for p in refined.split("\n\n") if p.strip()]
            if len(paragraphs) > 2:
                refined = paragraphs[0] + "\n\n" + paragraphs[1] + "\n\nBest regards,"

        # 2. Add CBM / Freight note
        if any(w in instr_lower for w in ["cbm", "海运", "箱规", "运费", "freight"]):
            cbm_note = "• Packaging: 24 pcs/ctn, 0.052 CBM, GW 14.2 kg (Pallet-friendly for overseas container loading)."
            refined += f"\n\n**Logistics Note**:\n{cbm_note}"

        # 3. Add Custom Discount / Price Adjustment
        price_match = re.search(r"\$(\d+(?:\.\d+)?)", refinement_instruction)
        qty_match = re.search(r"(\d+)\s*(?:台|pcs|units)", refinement_instruction)
        if price_match or qty_match:
            p_val = price_match.group(0) if price_match else "$9.60"
            q_val = qty_match.group(1) if qty_match else "100"
            special_offer = f"**Special Management Approval**: For your order of **{q_val} pcs**, we can approve a direct project rate of **{p_val} FOB**."
            refined += f"\n\n{special_offer}"

        # 4. Add Factory Audit / Verification
        if any(w in instr_lower for w in ["验厂", "合规", "证书", "audit", "cert"]):
            cert_note = "• Factory Credentials: SGS/TÜV audited manufacturer, ISO 9001:2015, full CE & RoHS test reports available."
            refined += f"\n\n**Compliance Verification**:\n{cert_note}"

        return refined
