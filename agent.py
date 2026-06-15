"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re
import sys
from tools import search_listings, suggest_outfit, create_fit_card


def _new_session(query: str, wardrobe: dict) -> dict:
    """Initialize and return a fresh session dict for one user interaction."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # 1. Initialize the session dictionary matching our State Management spec
    session = {
        "query": query,
        "wardrobe": wardrobe,
        "results": [],
        "selected_item": None,
        "outfit_suggestion": "",
        "fit_card": "",
        "error": None,
    }

    # Guard: Check for empty or whitespace-only queries
    if not query or not query.strip():
        session["error"] = "Query cannot be empty."
        return session

    # 2. Extract implicit parameters from the raw user query text
    max_price = None
    price_match = sorted(list(set(map(float, re.findall(r'under\s*\$?\s*(\d+(?:\.\d+)?)', query.lower())))))
    if price_match:
        max_price = float(price_match[0])

    # Basic size extraction strategy matching our example test queries
    size = None
    size_tokens = ["xxs", "xs", "s", "m", "l", "xl", "xxl"]
    for token in size_tokens:
        if f"size {token}" in query.lower() or f" {token} " in f" {query.lower()} ":
            size = token.upper()
            break

    # Clean the query string to isolate description keywords
    description = query
    if max_price:
        description = re.sub(r'under\s*\$?\s*\d+(?:\.\d+)?', '', description, flags=re.IGNORECASE)
    if size:
        description = re.sub(r'size\s*' + re.escape(size), '', description, flags=re.IGNORECASE)
    
    description = " ".join(description.split())

    # 3. Branch 1: Search Execution
    print(f"[Agent] Executing search_listings with description='{description}', size={size}, max_price={max_price}")
    search_results = search_listings(description=description, size=size, max_price=max_price)
    
    # ─── STRETCH FEATURE: RETRY LOGIC WITH FALLBACK ───
    if not search_results and size is not None:
        print("[Agent] No results found with size filter. Retrying search without size restriction...")
        search_results = search_listings(description=description, size=None, max_price=max_price)
        if search_results:
            session["error"] = f"⚠️ Note: We couldn't find anything in size {size}, so we expanded the search to all sizes!"

    if not search_results and max_price is not None:
        # Loosen budget constraint by 50% as a secondary fallback strategy
        adjusted_price = max_price * 1.5
        print(f"[Agent] Still no results. Retrying search with relaxed budget up to ${adjusted_price:.2f} and no size limit...")
        search_results = search_listings(description=description, size=None, max_price=adjusted_price)
        if search_results:
            session["error"] = f"⚠️ Note: No options found under ${max_price:.2f}. Showing items up to ${adjusted_price:.2f} in all sizes."
    # ──────────────────────────────────────────────────

    # Check if results list is empty (Branch Path Final Failure Mode)
    if not search_results:
        session["error"] = "No matching items found. Try loosening your search filters (e.g., higher price or broader description)."
        print("[Agent] Error branch encountered: Zero search listings. Terminating loop early.")
        return session

    # Commit results and pull top item to state
    session["results"] = search_results
    session["selected_item"] = search_results[0]
    print(f"[Agent] Success: Selected item '{session['selected_item']['title']}'")

    # 4. Branch 2: Outfit Styling
    print("[Agent] Passing selected_item into suggest_outfit tool...")
    outfit_text = suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"])
    session["outfit_suggestion"] = outfit_text

    # 5. Branch 3: Content Creation
    if not outfit_text or "Error" in outfit_text:
        session["fit_card"] = "Error: Cannot generate a fit card because the outfit recommendation is invalid."
        return session

    print("[Agent] Synthesizing shareable social media caption via create_fit_card...")
    caption_text = create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])
    session["fit_card"] = caption_text

    print("[Agent] Planning loop successfully finished processing.")
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"] and not session["selected_item"]:
        print(f"Error: {session['error']}")
    else:
        if session["error"]:
            print(f"Notification: {session['error']}\n")
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")