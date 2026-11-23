import pytest
from core.dst import DialogueStateTracker, DialogueState


def test_dst_session_isolation():
    dst = DialogueStateTracker()
    state1 = dst.get_or_create("session_buyer_a")
    state2 = dst.get_or_create("session_buyer_b")

    dst.update_from_buyer_message("session_buyer_a", "I need 400 pcs downlight for Dubai project.")
    dst.update_from_buyer_message("session_buyer_b", "Can I get 2 pcs samples of fan light to US?")

    assert state1.quantity == 400
    assert state1.product == "downlight"
    assert "Dubai" in state1.destination_zip

    assert state2.sample_quantity == 2
    assert state2.product == "fan_light"
    assert state2.quantity is None


def test_dst_slot_removal():
    dst = DialogueStateTracker()
    session_id = "test_sess"
    dst.update_from_buyer_message(session_id, "We need 500 pcs downlights with DALI-2 dimming to Germany.")
    
    state = dst.get_or_create(session_id)
    assert state.quantity == 500
    assert state.dimming == "DALI-2"
    assert state.destination_zip == "Germany"

    # Remove dimming slot
    dst.remove_slot(session_id, "dimming")
    assert state.dimming is None
    assert state.quantity == 500  # Other slots preserved

    # Remove quantity slot
    dst.remove_slot(session_id, "bulk_quantity")
    assert state.quantity is None


def test_dst_quantity_discrimination():
    dst = DialogueStateTracker()
    # Ensure sample quantity doesn't overwrite bulk quantity
    state = dst.update_from_buyer_message("sess_1", "Our bulk order is 1000 pcs, but first send 2 samples for testing.")
    assert state.quantity == 1000
    assert state.sample_quantity == 2



@pytest.mark.parametrize("message,quantity,samples", [
    ("We use E26/E27 bulbs, ship to ZIP 90001. Trial run of 300 pcs.", 300, None),
    ("Please ship 2 samples of an 18W downlight; our ZIP is 90001.", None, 2),
    ("We need ISO 9001 and accept USD 10.50.", None, None),
    ("Your MOQ shows 100 pcs. Can we start with 20 pcs?", 20, None),
    ("Quantity is 150 with 0-10V dimming.", 150, None),
])
def test_qty_extraction_ignores_unrelated_numbers(message, quantity, samples):
    state = DialogueStateTracker().update_from_buyer_message("buyer", message)
    assert state.quantity == quantity
    assert state.sample_quantity == samples
