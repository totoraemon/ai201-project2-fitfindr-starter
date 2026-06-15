"""
app.py

Gradio interface for FitFindr.
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """
    Called by Gradio when the user submits a query.
    """
    # 1. Guard against an empty query (return early with an error message)
    if not user_query or not user_query.strip():
        return "⚠️ Error: What are you looking for? Please input search keywords before clicking find.", "", ""

    # 2. Select the wardrobe dataset dictionary based on user's radio selection option
    if wardrobe_choice == "Example wardrobe":
        selected_wardrobe = get_example_wardrobe()
    else:
        selected_wardrobe = get_empty_wardrobe()

    # 3. Call run_agent() with the sanitized query text and chosen wardrobe mapping
    session_state = run_agent(user_query, selected_wardrobe)

    # 4. Critical Guard: If no item was selected at all, show the final hard failure
    if session_state.get("selected_item") is None:
        error_display = f"❌ No Results Found\n\n{session_state.get('error', 'Unknown error matching criteria.')}"
        return error_display, "", ""

    # 5. Parse selected_item data parameters out cleanly into a scannable item display card
    item = session_state["selected_item"]
    
    # Prepend the notification banner if a stretch feature fallback occurred
    warning_prefix = ""
    if session_state.get("error") is not None:
        warning_prefix = f"{session_state['error']}\n\n{'─' * 40}\n\n"

    listing_text = (
        f"{warning_prefix}"
        f"🎯 TITLE: {item.get('title')}\n"
        f"💰 PRICE: ${item.get('price'):.2f}\n"
        f"🏷️ BRAND: {item.get('brand') or 'N/A'}\n"
        f"📏 SIZE: {item.get('size')}\n"
        f"✨ CONDITION: {item.get('condition')}\n"
        f"🌐 PLATFORM: {item.get('platform').upper()}\n\n"
        f"📝 DESCRIPTION: {item.get('description')}"
    )

    # Return the clean 3-tuple mapped directly to the frontend text box panels
    return (
        listing_text, 
        session_state.get("outfit_suggestion", ""), 
        session_state.get("fit_card", "")
    )


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]

def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=8,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=8,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=8,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()