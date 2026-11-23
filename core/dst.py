"""
Multi-turn B2B Dialogue State Tracker (DST)
Manages cross-turn business slots (product category, bulk quantity, sample quantity,
voltage, dimming protocol, destination country/zip, and negotiation stage) with
window-level session isolation.
"""

import re
from typing import Dict, Any, List, Optional


class DialogueState:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.product: Optional[str] = None          # "downlight" | "fan_light" | "led_driver" | "general"
        self.product_name: Optional[str] = None     # Display name
        self.quantity: Optional[int] = None         # Bulk quantity (e.g. 50, 100, 400)
        self.sample_quantity: Optional[int] = None  # Sample quantity (e.g. 1, 2, 5)
        self.voltage: Optional[str] = None          # e.g. "110V", "220V", "AC 85-265V"
        self.dimming: Optional[str] = None          # e.g. "0-10V", "DALI-2", "TRIAC"
        self.destination_zip: Optional[str] = None  # e.g. "US 90001", "Dubai", "Germany"
        self.stage: str = "inquiry"                # "inquiry" | "price_negotiation" | "sample_stage" | "closing"
        self.turn_count: int = 0
        self.history: List[Dict[str, str]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "product": self.product,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "bulk_quantity": self.quantity,
            "sample_quantity": self.sample_quantity,
            "voltage": self.voltage,
            "dimming": self.dimming,
            "destination_zip": self.destination_zip,
            "stage": self.stage,
            "turn_count": self.turn_count,
            "history_length": len(self.history),
        }

    def remove_slot(self, slot_name: str):
        if slot_name in ("product", "product_name"):
            self.product = None
            self.product_name = None
        elif slot_name in ("quantity", "bulk_quantity"):
            self.quantity = None
        elif slot_name == "sample_quantity":
            self.sample_quantity = None
        elif slot_name == "voltage":
            self.voltage = None
        elif slot_name == "dimming":
            self.dimming = None
        elif slot_name in ("destination_zip", "destination", "zip"):
            self.destination_zip = None
        elif hasattr(self, slot_name):
            setattr(self, slot_name, None)

    def summary(self) -> str:
        parts = []
        if self.product_name:
            parts.append(f"Category: {self.product_name}")
        if self.quantity:
            parts.append(f"Bulk: {self.quantity} pcs")
        if self.sample_quantity:
            parts.append(f"Sample: {self.sample_quantity} pcs")
        if self.voltage:
            parts.append(f"Voltage: {self.voltage}")
        if self.dimming:
            parts.append(f"Dimming: {self.dimming}")
        if self.destination_zip:
            parts.append(f"Destination: {self.destination_zip}")
        parts.append(f"Stage: {self.stage}")
        return " | ".join(parts)


class DialogueStateTracker:
    def __init__(self):
        self.sessions: Dict[str, DialogueState] = {}

    def get_or_create(self, session_id: str = "default") -> DialogueState:
        if session_id not in self.sessions:
            self.sessions[session_id] = DialogueState(session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str = "default"):
        self.sessions[session_id] = DialogueState(session_id)

    def clear(self):
        self.sessions.clear()

    def remove_slot(self, session_id: str, slot_name: str) -> DialogueState:
        state = self.get_or_create(session_id)
        state.remove_slot(slot_name)
        return state

    def update_from_buyer_message(self, session_id: str, message: str, intent: Optional[Dict[str, Any]] = None) -> DialogueState:
        state = self.get_or_create(session_id)
        msg_lower = message.lower()
        state.turn_count += 1
        state.history.append({"role": "buyer", "text": message})

        # 1. Product Category Identification with strict word boundaries
        if re.search(r"\b(?:downlight|downlights|spotlight|spotlights|hotel lighting|recessed|cutout|ugr|cob)\b", msg_lower) or any(c in msg_lower for c in ["筒灯", "射灯", "工程灯"]):
            if state.product != "downlight":
                state.product = "downlight"
                state.product_name = "Architectural Downlights (LT-DL01)"
        elif re.search(r"\b(?:fan|fan light|socket fan|ceiling fan|blades|breezeglow|e27 fan|e26 fan)\b", msg_lower) or any(c in msg_lower for c in ["风扇灯", "螺口风扇", "插座风扇"]):
            if state.product != "fan_light":
                state.product = "fan_light"
                state.product_name = "Foldable Socket Fan Light (LT-SF30)"
        elif re.search(r"\b(?:driver|power supply|ballast|triac driver|dali driver|constant current|ripple free)\b", msg_lower) or any(c in msg_lower for c in ["电源", "驱动", "调光电源"]):
            if state.product != "led_driver":
                state.product = "led_driver"
                state.product_name = "ProDrive LED Driver (LT-DRV)"

        # 2. Quantity Extraction (Distinguish Sample vs Bulk)
        sample_match = re.search(r"\b(?:sample|samples|test|trial)\s*(?:of)?\s*(\d+)\s*(?:pcs|units|pieces)?\b", msg_lower)
        if not sample_match:
            sample_match = re.search(r"\b(\d+)\s*(?:pcs|pieces|units)?\s*(?:for\s*)?(?:sample|samples|testing)\b", msg_lower)

        if sample_match:
            try:
                sq = int(sample_match.group(1))
                if 1 <= sq <= 20:
                    state.sample_quantity = sq
            except ValueError:
                pass

        bulk_matches = re.finditer(
            r"(?<![\w.$-])([1-9]\d{0,5})\s*(?:pcs|units|pieces|sets|cartons|ctns|台|件)\b",
            msg_lower,
        )
        for match in bulk_matches:
            if sample_match and match.start() < sample_match.end() and sample_match.start() < match.end():
                continue
            preceding = msg_lower[:match.start()]
            if re.search(r"\bmoq\s*(?:shows|is|of|:)?\s*$", preceding):
                continue
            state.quantity = int(match.group(1))
            break

        else:
            labeled_quantity = re.search(
                r"\b(?:bulk quantity|order quantity|quantity|qty)\s*(?:(?:is|of)\s*|:\s*)?([1-9]\d{0,5})(?![\w.])",
                msg_lower,
            )
            if labeled_quantity:
                state.quantity = int(labeled_quantity.group(1))

        # 3. Voltage Specification
        if re.search(r"\b110\s*v(?:olts?)?\b", msg_lower):
            state.voltage = "110V (60Hz)"
        elif re.search(r"\b220\s*v(?:olts?)?\b", msg_lower):
            state.voltage = "220-240V (50Hz)"
        elif re.search(r"\b(?:universal|wide voltage|85-265v)\b", msg_lower):
            state.voltage = "AC 85-265V Universal"

        # 4. Dimming Protocol
        if re.search(r"\bdali(?:-2)?\b", msg_lower):
            state.dimming = "DALI-2"
        elif re.search(r"\b0-10v\b", msg_lower) or re.search(r"\b1-10v\b", msg_lower):
            state.dimming = "0-10V Dimming"
        elif re.search(r"\btriac\b", msg_lower) or re.search(r"\bphase cut\b", msg_lower):
            state.dimming = "TRIAC Phase Dimming"

        # 5. Destination country / Zip
        zip_match = re.search(r"\b(?:to|in|ship to|zip|destination)\s*:?\s*([a-z]{2}\s*\d{4,6}|\d{5})\b", msg_lower)
        if zip_match:
            state.destination_zip = zip_match.group(1).upper()
        elif re.search(r"\b(?:dubai|uae)\b", msg_lower):
            state.destination_zip = "Dubai, UAE"
        elif re.search(r"\b(?:germany|deutschland)\b", msg_lower):
            state.destination_zip = "Germany"
        elif re.search(r"\b(?:usa|united states|california|los angeles)\b", msg_lower):
            state.destination_zip = "United States"

        # 6. Negotiation Stage
        if state.sample_quantity and not state.quantity:
            state.stage = "sample_stage"
        elif intent and intent.get("is_price_objection"):
            state.stage = "price_negotiation"
        elif state.quantity and state.destination_zip:
            state.stage = "closing"
        else:
            state.stage = "inquiry"

        return state
