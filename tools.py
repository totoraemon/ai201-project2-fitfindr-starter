"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re
from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    def search_listings(
        description: str,
        size: str | None = None,
        max_price: float | None = None,
    ) -> list[dict]:
        """
        Search the mock listings dataset for items matching the description,
        optional size, and optional price ceiling.
        """
    # 1. Load all listings using the helper function
    listings = load_listings()
    filtered_listings = []

    # Prepare search tokens for description matching
    search_tokens = set(re.findall(r'\w+', description.lower()))

    for item in listings:
        # 2. Filter by max_price (inclusive) if provided
        if max_price is not None and item.get("price", 0) > max_price:
            continue

        # Filter by size (case-insensitive substring match) if provided
        if size is not None:
            item_size = str(item.get("size", "")).lower()
            target_size = size.lower()
            if target_size not in item_size:
                continue

        # 3. Score each remaining listing by keyword overlap with `description`
        # Check against title, description, and style tags
        item_text = (
            str(item.get("title", "")) + " " + 
            str(item.get("description", "")) + " " + 
            " ".join(item.get("style_tags", []))
        ).lower()
        
        item_tokens = set(re.findall(r'\w+', item_text))
        overlap = search_tokens.intersection(item_tokens)
        score = len(overlap)

        # 4. Drop any listings with a score of 0 (no relevant matches)
        if score > 0:
            # Temporarily attach score for sorting
            item_copy = dict(item)
            item_copy["_score"] = score
            filtered_listings.append(item_copy)

    # 5. Sort by score, highest first, and clean up the temporary score key
    filtered_listings.sort(key=lambda x: x["_score"], reverse=True)
    for item in filtered_listings:
        item.pop("_score", None)

    return filtered_listings


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    if not new_item:
        return "No item was provided to style."

    client = _get_groq_client()
    wardrobe_items = wardrobe.get("items", [])

    # 1. Check whether wardrobe['items'] is empty
    if not wardrobe_items:
        # 2. If empty: call the LLM with a prompt for general styling ideas
        prompt = (
            f"You are a trendy fashion stylist. A user is considering purchasing the following item:\n"
            f"Item: {new_item.get('title')}\n"
            f"Description: {new_item.get('description')}\n"
            f"Category: {new_item.get('category')}\n"
            f"Style Tags: {', '.join(new_item.get('style_tags', []))}\n\n"
            f"The user's personal wardrobe is currently empty. Please provide general, highly creative styling ideas "
            f"for this piece. What kinds of items, silhouettes, and color palettes pair well with it? What kind of vibe "
            f"or aesthetic does it suit best? Give 1-2 practical suggestions."
        )
    else:
        # 3. If not empty: format the wardrobe items into a prompt
        wardrobe_str = ""
        for idx, w_item in enumerate(wardrobe_items, 1):
            wardrobe_str += (
                f"{idx}. {w_item.get('name')} (Category: {w_item.get('category')}, "
                f"Colors: {', '.join(w_item.get('colors', []))}, Tags: {', '.join(w_item.get('style_tags', []))})\n"
            )

        prompt = (
            f"You are a personal wardrobe stylist. A user wants to style a new item into their closet:\n"
            f"New Item: {new_item.get('title')} (${new_item.get('price')} from {new_item.get('platform')})\n"
            f"New Item Description: {new_item.get('description')}\n"
            f"New Item Tags: {', '.join(new_item.get('style_tags', []))}\n\n"
            f"Here is their existing wardrobe:\n{wardrobe_str}\n"
            f"Suggest 1–2 complete, cohesive outfit combinations using the new item paired with explicitly named "
            f"pieces from their wardrobe. Be specific about the look, layering, and overall aesthetic vibe."
        )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an authentic, cool personal fashion assistant. Keep your responses crisp, direct, and stylish."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        # 4. Return the LLM's response as a string
        response_text = completion.choices[0].message.content
        return response_text.strip() if response_text else "Could not generate styling ideas."
    
    except Exception as e:
        # Graceful fallback instead of throwing an unhandled exception
        return (
            f"Styling Tip: This {new_item.get('category', 'item')} matches a "
            f"{', '.join(new_item.get('style_tags', ['classic']))} aesthetic. Pair it with complementary "
            f"neutral staples from your closet!"
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    # 1. Guard against an empty or whitespace-only outfit string
    if not outfit or not outfit.strip():
        return "Error: Cannot generate a fit card without a valid outfit recommendation description."
    if not new_item:
        return "Error: Missing item metadata."

    client = _get_groq_client()

    # 2. Build a prompt containing item details and the outfit context
    prompt = (
        f"Create a short, shareable social media outfit caption (like Instagram or TikTok) based on this find:\n"
        f"Item Name: {new_item.get('title')}\n"
        f"Price: ${new_item.get('price')}\n"
        f"Platform: {new_item.get('platform')}\n"
        f"Outfit Suggestion: {outfit}\n\n"
        f"Guidelines:\n"
        f"- Must be exactly 2–4 sentences long.\n"
        f"- Feel casual, authentic, and modern (like a real OOTD post, not an ad or catalog description).\n"
        f"- Mention the item name, price, and platform naturally exactly once each.\n"
        f"- Capture the vibe in descriptive terms.\n"
        f"- Write in lowercase or use emojis if it fits a casual aesthetic naturally."
    )

    try:
        # 3. Call the LLM with an elevated temperature (1.0) to maximize variation
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Gen-Z fashion influencer writing a casual outfit caption."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            max_tokens=150
        )
        response_text = completion.choices[0].message.content
        return response_text.strip() if response_text else "Error: Failed to synthesize caption."
    
    except Exception as e:
        return f"thrifted this {new_item.get('title')} on {new_item.get('platform')} for ${new_item.get('price')}! absolute steal. 🛍️✨"
