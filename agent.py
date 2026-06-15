"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import sys
from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
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
    # (A basic parser looking for price patterns like 'under $30' or 'under 30')
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
    
    # Check if results list is empty (Branch Path Failure Mode)
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

    import re
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")

    # Test Case 1: Standard Valid Interaction Walkthrough Flow
    print("=== RUNNING TEST CASE 1: VALID FLOW ===")
    test_query = "vintage graphic tee under $30"
    res_session = run_agent(test_query, get_example_wardrobe())
    
    print("\n--- State flow Verification ---")
    print(f"Selected Item ID: {res_session['selected_item']['id'] if res_session['selected_item'] else None}")
    print(f"Outfit Generated: {res_session['outfit_suggestion'][:60]}...")
    print(f"Fit Card Caption: {res_session['fit_card']}\n")

    # Test Case 2: No-Results Early Failure Branch Path
    print("=== RUNNING TEST CASE 2: NO-RESULTS BRANCH ===")
    bad_query = "designer ballgown size XXS under $5"
    fail_session = run_agent(bad_query, get_example_wardrobe())
    
    print("\n--- Failure Verification ---")
    print(f"Session Error Status: {fail_session['error']}")
    print(f"Should be None (Selected Item): {fail_session['selected_item']}")
    print(f"Should be empty (Fit Card): '{fail_session['fit_card']}'")
    assert fail_session["error"] is not None
    assert fail_session["selected_item"] is None
