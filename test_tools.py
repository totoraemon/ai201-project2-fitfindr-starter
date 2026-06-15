# tests/test_tools.py

import pytest
from tools import search_listings, suggest_outfit, create_fit_card

# ── Mock Objects for Testing ──────────────────────────────────────────────────

@pytest.fixture
def mock_item():
    return {
        "id": "lst_099",
        "title": "Vintage Faded Carhartt Jacket",
        "description": "Perfectly broken-in workwear canvas jacket in duck brown.",
        "category": "outerwear",
        "style_tags": ["vintage", "workwear", "streetwear"],
        "size": "L",
        "condition": "good",
        "price": 45.00,
        "colors": ["brown"],
        "brand": "Carhartt",
        "platform": "depop"
    }

@pytest.fixture
def mock_empty_wardrobe():
    return {"items": []}

@pytest.fixture
def mock_populated_wardrobe():
    return {
        "items": [
            {
                "id": "w_901",
                "name": "Relaxed fit black cargo pants",
                "category": "bottoms",
                "colors": ["black"],
                "style_tags": ["streetwear", "cargo"]
            }
        ]
    }


# ── Search Listing Tests ──────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []  # Verifies clean return instead of raising an exception

def test_search_price_filter():
    results = search_listings("pants", size=None, max_price=30)
    assert all(item["price"] <= 30 for item in results)

def test_search_case_insensitive_size():
    # 'S/M' layout in mock data should catch on a request for 'M'
    results = search_listings("baby tee", size="M", max_price=40)
    assert len(results) > 0
    assert "m" in results[0]["size"].lower()


# ── Outfit Suggestion Tests ───────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe(mock_item, mock_empty_wardrobe):
    # Evaluates graceful pivot to aesthetic styling advice on empty closets
    response = suggest_outfit(mock_item, mock_empty_wardrobe)
    assert isinstance(response, str)
    assert len(response) > 0
    # Check that it generated general advice language instead of throwing errors
    assert "vibe" in response.lower() or "pair" in response.lower() or "Styling" in response

def test_suggest_outfit_populated_wardrobe(mock_item, mock_populated_wardrobe):
    response = suggest_outfit(mock_item, mock_populated_wardrobe)
    assert isinstance(response, str)
    assert len(response) > 0


# ── Fit Card Tests ────────────────────────────────────────────────────────────

def test_create_fit_card_empty_guard(mock_item):
    # Ensure tool structural guards capture invalid white space gracefully
    response = create_fit_card("   ", mock_item)
    assert "Error" in response

def test_create_fit_card_success(mock_item):
    outfit_context = "Wear the Carhartt jacket with relaxed black cargo pants and chunky skate shoes."
    response = create_fit_card(outfit_context, mock_item)
    assert isinstance(response, str)
    assert len(response) > 0