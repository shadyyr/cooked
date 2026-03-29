import json
import sys
from urllib.error import URLError, HTTPError

from quantities import format_quantity_display
from recipes import suggest_recipes, display_suggestions_paginated
from api import fetch_mealdb_recipes
from cli import get_ingredients, add_more_ingredients, edit_ingredients
from fallbacks import FALLBACK_RECIPES

API_RESULT_LIMIT = 12
DISPLAY_BATCH_SIZE = 3
MIN_MATCH_SCORE = 0.30

if __name__ == "__main__":
    user_ingredients = get_ingredients(FALLBACK_RECIPES)

    while True:
        print("\nYour ingredients:")
        for ing, qty in user_ingredients.items():
            print(f"- {ing}: {format_quantity_display(qty)}")
        print(f"\nTotal ingredients: {len(user_ingredients)}")

        try:
            api_recipes = fetch_mealdb_recipes(user_ingredients, limit=API_RESULT_LIMIT)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            api_recipes = {}

        recipes_to_use = api_recipes if api_recipes else FALLBACK_RECIPES
        source_label = "TheMealDB" if api_recipes else "local fallback data"

        print(f"\nUsing recipe source: {source_label}")

        suggestions = suggest_recipes(user_ingredients, recipes_to_use, min_score=MIN_MATCH_SCORE)
        next_action = display_suggestions_paginated(suggestions, min_match_score=MIN_MATCH_SCORE, batch_size=DISPLAY_BATCH_SIZE)

        if not sys.stdin.isatty():
            break

        if next_action == "add_ingredients":
            user_ingredients = add_more_ingredients(user_ingredients, FALLBACK_RECIPES)
            continue
        if next_action == "edit_ingredients":
            user_ingredients = edit_ingredients(user_ingredients, FALLBACK_RECIPES)
            continue

        next_step = input(
            "\nWould you like to [A]dd ingredients, [E]dit ingredients, or [N]o to finish? [A/E/N]: "
        ).strip().lower()
        if next_step in {"a", "add", "y", "yes"}:
            user_ingredients = add_more_ingredients(user_ingredients, FALLBACK_RECIPES)
            continue
        if next_step in {"e", "edit"}:
            user_ingredients = edit_ingredients(user_ingredients, FALLBACK_RECIPES)
            continue
        if next_step not in {"n", "no", ""}:
            print("Unknown choice. Ending session.")
            break
        break
