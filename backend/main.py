import json
import re
import sys
from urllib import parse, request
from urllib.error import URLError, HTTPError
from quantities import (
    UNIT_MAP,
    UNIT_CONVERSIONS_TO_BASE,
    parse_quantity,
    format_amount_unit,
    format_quantity_display,
    list_valid_units_text,
    damerau_levenshtein,
    find_best_text_match,
    suggest_unit_correction,
    validate_quantity_input,
    convert_amount_between_units,
    combine_quantities,
    parse_amount_unit,
    is_quantity_sufficient,
    compute_short_by,
)
from ingredients import (
    CURATED_COMMON_INGREDIENTS,
    API_SEEN_INGREDIENTS,
    PLURAL_MAP,
    normalize_ingredient,
    is_valid_ingredient,
    ingredient_syntax_reason,
    get_ingredient_vocabulary,
    suggest_ingredient_correction,
    assess_ingredient_confidence,
    resolve_ingredient_input_with_guidance,
)
from recipes import (
    can_make_recipe,
    suggest_recipes,
    print_suggestion,
    display_suggestions_paginated
)

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
API_RESULT_LIMIT = 12
DISPLAY_BATCH_SIZE = 3
MIN_MATCH_SCORE = 0.30

# Local fallback recipes (used when API has no results / request fails)
FALLBACK_RECIPES = {
    'scrambled eggs': {
        'egg': '2',
        'milk': '0.25 cup',
        'butter': '1 tbsp'
    },
    'grilled cheese': {
        'bread': '2 slice',
        'cheese': '2 slice',
        'butter': '1 tbsp'
    },
    'pasta tomato': {
        'pasta': '200 g',
        'canned tomato': '1 can',
        'olive oil': '1 tbsp',
        'garlic': '1 clove'
    },
    'simple salad': {
        'lettuce': '1 piece',
        'tomato': '1 piece',
        'olive oil': '1 tbsp'
    },

    'omelette': {
        'egg': '3',
        'milk': '2 tbsp',
        'butter': '1 tsp'
    },
    'french toast': {
        'bread': '2 slice',
        'egg': '2',
        'milk': '0.25 cup',
        'butter': '1 tbsp'
    },
    'garlic bread': {
        'bread': '4 slice',
        'butter': '2 tbsp',
        'garlic': '2 clove'
    },
    'cheese omelette': {
        'egg': '2',
        'cheese': '1 slice',
        'butter': '1 tsp'
    },
    'buttered pasta': {
        'pasta': '150 g',
        'butter': '1 tbsp',
        'salt': '1 tsp'
    },
    'aglio e olio': {
        'pasta': '200 g',
        'olive oil': '2 tbsp',
        'garlic': '3 clove'
    },
    'tomato pasta': {
        'pasta': '200 g',
        'tomato': '2 piece',
        'olive oil': '1 tbsp',
        'garlic': '1 clove'
    },
    'cheese quesadilla': {
        'cheese': '2 slice',
        'butter': '1 tbsp'
    },
    'pan fried potatoes': {
        'potato': '2 piece',
        'olive oil': '1 tbsp',
        'salt': '1 tsp'
    },
    'roasted potatoes': {
        'potato': '3 piece',
        'olive oil': '1 tbsp'
    },
    'sauteed mushrooms': {
        'mushroom': '200 g',
        'butter': '1 tbsp',
        'garlic': '1 clove'
    },
    'fruit bowl': {
        'apple': '1 piece',
        'banana': '1 piece'
    },
    'strawberry banana bowl': {
        'strawberry': '1 cup',
        'banana': '1 piece'
    }
}

def mealdb_get_json(url):
    req = request.Request(url, headers={"User-Agent": "cooked-backend/1.0"})
    with request.urlopen(req, timeout=8) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)


def search_meal_ids_by_ingredient(ingredient):
    encoded = parse.quote(ingredient)
    url = f"{MEALDB_BASE_URL}/filter.php?i={encoded}"
    payload = mealdb_get_json(url)
    meals = payload.get("meals") or []
    return {m["idMeal"] for m in meals if m.get("idMeal")}


def lookup_meal_detail(meal_id):
    encoded = parse.quote(str(meal_id))
    url = f"{MEALDB_BASE_URL}/lookup.php?i={encoded}"
    payload = mealdb_get_json(url)
    meals = payload.get("meals") or []
    return meals[0] if meals else None


def extract_ingredients_from_meal(meal):
    requirements = {}
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if not ing:
            continue
        normalized_ing = normalize_ingredient(ing)
        API_SEEN_INGREDIENTS.add(normalized_ing)
        req_qty = measure if measure else "1"
        requirements[normalized_ing] = req_qty
    return requirements


def fetch_mealdb_recipes(pantry, limit=API_RESULT_LIMIT):
    """
    Builds candidate recipes from TheMealDB using pantry ingredient overlap.
    """
    ingredient_hits = {}

    for ingredient in pantry.keys():
        try:
            ids = search_meal_ids_by_ingredient(ingredient)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            continue
        for meal_id in ids:
            ingredient_hits[meal_id] = ingredient_hits.get(meal_id, 0) + 1

    if not ingredient_hits:
        return {}

    top_ids = sorted(ingredient_hits.keys(), key=lambda meal_id: ingredient_hits[meal_id], reverse=True)[:limit]
    recipes = {}
    for meal_id in top_ids:
        try:
            meal = lookup_meal_detail(meal_id)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            continue
        if not meal:
            continue
        recipe_name = meal.get("strMeal", f"Meal {meal_id}").strip()
        requirements = extract_ingredients_from_meal(meal)
        if requirements:
            recipes[recipe_name] = requirements

    return recipes

def get_ingredients():
    """
    Prompts the user to input ingredients they have in their pantry.
    Validates that inputs are actual ingredients.
    Returns a dict of ingredient name to quantity.
    """
    ingredients = {}
    interactive = sys.stdin.isatty()
    if interactive:
        print("Enter the ingredients you have in your pantry.")
        print("Type 'done' when you are finished entering ingredients.")

    while True:
        ingredient_prompt = "Ingredient: " if interactive else ""
        ingredient = input(ingredient_prompt).strip().lower()
        if ingredient == 'done':
            break
        if not ingredient:
            print("Please enter a valid ingredient or 'done' to finish.")
            continue

        # 3-layer ingredient validation
        if interactive:
            normalized, confidence = resolve_ingredient_input_with_guidance(
                ingredient, FALLBACK_RECIPES, prompt_label="Ingredient"
            )
            if normalized == "done":
                break
            if confidence == "suspicious":
                print(f"Accepted uncommon ingredient: {normalized}")
        else:
            assessment = assess_ingredient_confidence(ingredient, FALLBACK_RECIPES)
            if assessment["status"] == "invalid":
                print(f"Skipping invalid ingredient '{ingredient}': {assessment['reason']}")
                continue
            normalized = assessment["normalized"]
            if assessment["status"] == "suspicious":
                hint = f" Suggestion: {assessment['suggestion']}." if assessment["suggestion"] else ""
                print(f"Uncommon ingredient '{ingredient}' accepted as '{normalized}'.{hint}")

        quantity_prompt = "Quantity (e.g. 2 cup, 250 ml, 3 slice): " if interactive else ""
        quantity_input = input(quantity_prompt).strip()
        while True:
            if not quantity_input:
                if interactive:
                    print("Please provide a quantity for this ingredient.")
                quantity_input = input(quantity_prompt).strip()
                continue

            valid_quantity, error = validate_quantity_input(quantity_input)
            if valid_quantity:
                break

            print(error)
            print(f"Valid measurement units: {list_valid_units_text()}")
            quantity_input = input(quantity_prompt).strip()

        quantity = parse_quantity(quantity_input)
        formatted_input = format_quantity_display(quantity)

        if normalized in ingredients:
            combined_quantity, target_unit = combine_quantities(ingredients[normalized], quantity)
            if combined_quantity is None:
                print(
                    f"Could not safely combine '{ingredients[normalized]}' with '{formatted_input}' for {normalized}. "
                    "Keeping existing quantity."
                )
                continue
            ingredients[normalized] = combined_quantity
            if target_unit and parse_amount_unit(quantity)[1] and parse_amount_unit(quantity)[1] != target_unit:
                print(f"Converted and updated: {normalized} ({combined_quantity})")
            else:
                print(f"Updated: {normalized} ({combined_quantity})")
        else:
            ingredients[normalized] = formatted_input
            print(f"Added: {normalized} ({formatted_input})")

    return ingredients


def add_more_ingredients(existing_ingredients):
    """
    Lets the user add more ingredients after initial suggestions.
    Updates quantities if an ingredient already exists.
    """
    print("\nAdd more ingredients to improve suggestions.")
    print("Type 'done' when finished adding more ingredients.")

    while True:
        ingredient = input("Additional ingredient: ").strip().lower()
        if ingredient == "done":
            break
        if not ingredient:
            print("Please enter a valid ingredient or 'done' to finish.")
            continue

        normalized, confidence = resolve_ingredient_input_with_guidance(
            ingredient,
            FALLBACK_RECIPES,
            prompt_label="Additional ingredient"
        )
        if normalized == "done":
            break
        if confidence == "suspicious":
            print(f"Accepted uncommon ingredient: {normalized}")

        quantity_prompt = "Quantity (e.g. 2 cup, 250 ml, 3 slice): "
        quantity_input = input(quantity_prompt).strip()
        while True:
            if not quantity_input:
                print("Please provide a quantity for this ingredient.")
                quantity_input = input(quantity_prompt).strip()
                continue

            valid_quantity, error = validate_quantity_input(quantity_input)
            if valid_quantity:
                break

            print(error)
            print(f"Valid measurement units: {list_valid_units_text()}")
            quantity_input = input(quantity_prompt).strip()

        quantity = parse_quantity(quantity_input)
        formatted_input = format_quantity_display(quantity)

        if normalized in existing_ingredients:
            previous_quantity = existing_ingredients[normalized]
            combined_quantity, target_unit = combine_quantities(previous_quantity, quantity)
            if combined_quantity is None:
                print(
                    f"Could not safely combine '{previous_quantity}' with '{formatted_input}' for {normalized}. "
                    "Keeping existing quantity."
                )
                continue
            existing_ingredients[normalized] = combined_quantity

            new_amt, new_unit = parse_amount_unit(quantity)
            if target_unit and new_unit and new_unit != target_unit:
                converted_amt = convert_amount_between_units(new_amt, new_unit, target_unit)
                converted_text = format_amount_unit(converted_amt, target_unit)
                print(f"Updated: {normalized} ({combined_quantity}) [converted {formatted_input} -> {converted_text}]")
            else:
                print(f"Updated: {normalized} ({combined_quantity})")
        else:
            existing_ingredients[normalized] = formatted_input
            print(f"Added: {normalized} ({formatted_input})")

    return existing_ingredients


def edit_ingredients(existing_ingredients):
    """
    Lets users edit ingredient name, quantity, or unit with conversion.
    """
    if not existing_ingredients:
        print("\nNo ingredients to edit.")
        return existing_ingredients

    print("\nEdit ingredient list.")
    print("Type 'done' at any prompt to finish editing.")

    while True:
        print("\nCurrent ingredients:")
        for ing, qty in existing_ingredients.items():
            print(f"- {ing}: {format_quantity_display(qty)}")

        target_name = input("\nIngredient to edit: ").strip().lower()
        if target_name == "done":
            break
        if not target_name:
            print("Please enter an ingredient name or 'done'.")
            continue

        normalized_target = normalize_ingredient(target_name)
        if normalized_target not in existing_ingredients:
            print(f"'{target_name}' is not in your ingredient list.")
            continue

        edit_choice = input(
            "What do you want to edit? [N]ame, [Q]uantity, [M]easurement unit: "
        ).strip().lower()
        if edit_choice == "done":
            break

        if edit_choice in {"n", "name"}:
            new_name = input("New ingredient name: ").strip().lower()
            if new_name == "done":
                break
            if not new_name:
                print("Ingredient name cannot be empty.")
                continue

            normalized_new, confidence = resolve_ingredient_input_with_guidance(
                new_name,
                FALLBACK_RECIPES,
                prompt_label="New ingredient name"
            )
            if normalized_new == "done":
                break
            if confidence == "suspicious":
                print(f"Using uncommon ingredient name: {normalized_new}")

            current_qty = existing_ingredients[normalized_target]

            if normalized_new == normalized_target:
                print("Ingredient name is unchanged.")
                continue

            if normalized_new in existing_ingredients:
                merged_qty, _ = combine_quantities(existing_ingredients[normalized_new], current_qty)
                if merged_qty is None:
                    print(
                        f"Could not merge '{normalized_target}' into '{normalized_new}' due to incompatible units."
                    )
                    continue
                del existing_ingredients[normalized_target]
                existing_ingredients[normalized_new] = merged_qty
                print(f"Merged and renamed to: {normalized_new} ({merged_qty})")
            else:
                del existing_ingredients[normalized_target]
                existing_ingredients[normalized_new] = current_qty
                print(f"Renamed: {normalized_target} -> {normalized_new}")
            continue

        if edit_choice in {"q", "quantity"}:
            quantity_prompt = "New quantity (e.g. 2 cup, 250 ml, 4 slice): "
            new_quantity = input(quantity_prompt).strip()
            if new_quantity.lower() == "done":
                break
            while True:
                if not new_quantity:
                    print("Please provide a quantity.")
                    new_quantity = input(quantity_prompt).strip()
                    if new_quantity.lower() == "done":
                        break
                    continue

                valid_quantity, error = validate_quantity_input(new_quantity)
                if valid_quantity:
                    break

                print(error)
                print(f"Valid measurement units: {list_valid_units_text()}")
                new_quantity = input(quantity_prompt).strip()
                if new_quantity.lower() == "done":
                    break

            if new_quantity.lower() == "done":
                break

            formatted = format_quantity_display(new_quantity)
            existing_ingredients[normalized_target] = formatted
            print(f"Updated quantity: {normalized_target} ({formatted})")
            continue

        if edit_choice in {"m", "measurement", "measurement unit", "unit"}:
            current_qty = existing_ingredients[normalized_target]
            current_amt, current_unit = parse_amount_unit(current_qty)
            if current_amt is None or not current_unit:
                print(
                    f"Cannot change measurement unit for '{normalized_target}' because current quantity "
                    f"'{current_qty}' is not parseable with a known unit."
                )
                continue

            new_unit_raw = input("New measurement unit (e.g. cup, tbsp, ml, g): ").strip().lower()
            if new_unit_raw == "done":
                break
            if not new_unit_raw:
                print("Measurement unit cannot be empty.")
                continue

            new_unit = UNIT_MAP.get(new_unit_raw, new_unit_raw)
            if new_unit not in set(UNIT_MAP.values()):
                suggestion = suggest_unit_correction(new_unit_raw)
                if suggestion:
                    print(f"Invalid unit '{new_unit_raw}'. Did you mean '{suggestion}'?")
                else:
                    print(f"Invalid unit '{new_unit_raw}'.")
                print(f"Valid measurement units: {list_valid_units_text()}")
                continue
            converted_amt = convert_amount_between_units(current_amt, current_unit, new_unit)
            if converted_amt is None:
                print(f"Could not convert from '{current_unit}' to '{new_unit}'.")
                continue

            converted_qty = format_amount_unit(converted_amt, new_unit)
            existing_ingredients[normalized_target] = converted_qty
            print(
                f"Updated unit: {normalized_target} ({format_amount_unit(current_amt, current_unit)} -> {converted_qty})"
            )
            continue

        print("Invalid choice. Please choose name, quantity, or measurement unit.")

    return existing_ingredients

if __name__ == "__main__":
    user_ingredients = get_ingredients()

    while True:
        print("\nYour ingredients:")
        for ing, qty in user_ingredients.items():
            print(f"- {ing}: {format_quantity_display(qty)}")
        print(f"\nTotal ingredients: {len(user_ingredients)}")

        try:
            api_recipes = fetch_mealdb_recipes(user_ingredients)
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
            user_ingredients = add_more_ingredients(user_ingredients)
            continue
        if next_action == "edit_ingredients":
            user_ingredients = edit_ingredients(user_ingredients)
            continue

        next_step = input(
            "\nWould you like to [A]dd ingredients, [E]dit ingredients, or [N]o to finish? [A/E/N]: "
        ).strip().lower()
        if next_step in {"a", "add", "y", "yes"}:
            user_ingredients = add_more_ingredients(user_ingredients)
            continue
        if next_step in {"e", "edit"}:
            user_ingredients = edit_ingredients(user_ingredients)
            continue
        if next_step not in {"n", "no", ""}:
            print("Unknown choice. Ending session.")
            break
        break
