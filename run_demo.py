"""
Trade Desk Copilot - All-in-One Demo & CLI Walkthrough
Usage:
    python run_demo.py          # Interactive terminal simulation with 8 B2B buyer scenarios
    python run_demo.py --gui    # Launch floating desktop HUD workbench (requires PyQt5)
    python run_demo.py --card   # Generate sample 1080x1080 visual quotation card
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.agent import TradeDeskAgent, STYLE_NAMES, STYLE_GOLD_NEGOTIATION, STYLE_WHATSAPP_CONCISE, STYLE_ENGINEERING_SPEC
from core.mock_engine import MOCK_INQUIRIES
from core.card_generator import generate_sample_card


def print_banner():
    print("=" * 72)
    print("   LuminaTech Trade Desk Copilot · B2B Foreign Trade AI Workbench")
    print("   Multi-Turn DST · RAG Catalog Grounding · Host-Aware Formatting")
    print("=" * 72)


def run_cli_demo():
    print_banner()
    agent = TradeDeskAgent()

    print("\n[Available Synthetic B2B Scenarios]:")
    for i, s in enumerate(MOCK_INQUIRIES, 1):
        print(f"  [{i}] {s['title']} ({s['buyer_name']} | {s['app_hint']})")

    print("\nEnter scenario number [1-8] or press ENTER to run all scenarios sequentially:")
    choice = input("Select > ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(MOCK_INQUIRIES):
        selected_scenarios = [MOCK_INQUIRIES[int(choice) - 1]]
    else:
        selected_scenarios = MOCK_INQUIRIES[:3]  # Run first 3 by default

    for sc in selected_scenarios:
        print("\n" + "-" * 72)
        print(f"▶ SCENARIO: {sc['title']}")
        print(f"  Buyer: {sc['buyer_name']} | Host App: {sc['app_hint']}")
        print(f"  Message: \"{sc['message']}\"")
        print("-" * 72)

        res = agent.process_inquiry(
            buyer_message=sc["message"],
            session_id=f"cli_{sc['id']}",
            buyer_name=sc["buyer_name"],
            style=STYLE_GOLD_NEGOTIATION,
            target_app=sc["app_hint"]
        )

        print("\n[1. Buyer Intent & Classification]")
        print(f"  Tier: {res['intent']['tier']}")
        print(f"  Detected Scenarios: {', '.join(res['intent']['scenarios'])}")

        print("\n[2. Multi-Turn DST State Machine]")
        state = res["state"]
        print(f"  Product: {state.get('product_name')}")
        print(f"  Bulk Qty: {state.get('bulk_quantity')} | Sample Qty: {state.get('sample_quantity')}")
        print(f"  Dimming: {state.get('dimming')} | Destination: {state.get('destination_zip')}")
        print(f"  Negotiation Stage: {state.get('stage')}")

        print("\n[3. Grounded Knowledge Retrieval (Top Matches)]")
        for chunk in res["matched_references"][:2]:
            print(f"  • [{chunk['category']}] {chunk['title']} (Score: {chunk['score']})")

        print("\n[4. Synthesized B2B Negotiation Draft (Style: Gold Closing)]")
        print(res["english_reply"])

        print("\n[5. Host-Aware Cleaned Text for " + sc["app_hint"] + "]")
        print(res["formatted"]["text"])

    print("\n" + "=" * 72)
    print("Demo completed successfully. Run with --gui to experience the floating desktop pet!")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Trade Desk Copilot Demo Runner")
    parser.add_argument("--gui", action="store_true", help="Launch floating desktop GUI")
    parser.add_argument("--card", action="store_true", help="Generate sample 1080x1080 quotation card")
    args = parser.parse_args()

    if args.card:
        out_file = Path(__file__).resolve().parent / "assets" / "screenshots" / "sample_quotation_card.png"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        generate_sample_card(out_file)
        print(f"Quotation card successfully generated at: {out_file}")
    elif args.gui:
        from app.pet import run_pet_application
        run_pet_application()
    else:
        run_cli_demo()


if __name__ == "__main__":
    main()
