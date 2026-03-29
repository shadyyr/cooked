import sys
import re
from ingredients import normalize_ingredient
from quantities import is_quantity_sufficient, compute_short_by

GENERIC_INGREDIENT_FAMILIES = {
    "oil", "vinegar", "flour", "sugar", "rice", "milk", "cream", "cheese",
    "bean", "beans", "tomato", "pasta", "bread", "pepper", "onion", "garlic",
    "beef", "chicken", "pork", "fish", "butter",
}

MATCH_DESCRIPTOR_TOKENS = {
    "lean", "extra", "virgin", "fresh", "dried", "minced", "chopped", "sliced",
    "small", "medium", "large", "boneless", "skinless", "low-fat", "lowfat",
    "reduced-fat", "reduced", "organic", "raw", "cooked", "fat-free",
}


def _canonicalize_for_matching(ingredient_name):
    normalized = normalize_ingredient(ingredient_name or "")
    normalized = re.sub(r"[^a-z0-9\s/\-']", " ", normalized).strip()
    tokens = [t for t in normalized.split() if t]
    cleaned = []
    for token in tokens:
        if re.fullmatch(r"\d+\s*/\s*\d+", token):
            continue
        if token in MATCH_DESCRIPTOR_TOKENS:
            continue
        cleaned.append(token)
    return " ".join(cleaned).strip()


def _match_score(recipe_ingredient, pantry_ingredient):
    recipe_norm = normalize_ingredient(recipe_ingredient)
    pantry_norm = normalize_ingredient(pantry_ingredient)
    recipe_canon = _canonicalize_for_matching(recipe_norm)
    pantry_canon = _canonicalize_for_matching(pantry_norm)

    if pantry_norm == recipe_norm:
        return 100
    if recipe_canon and pantry_canon and pantry_canon == recipe_canon:
        return 90

    if pantry_norm.endswith(f" {recipe_norm}"):
        return 85
    if recipe_canon and pantry_canon and pantry_canon.endswith(f" {recipe_canon}"):
        return 80

    # One-way generic family matching:
    # recipe asks generic ingredient, pantry provides a specific variant.
    if recipe_norm in GENERIC_INGREDIENT_FAMILIES:
        haystack_norm = f" {pantry_norm} "
        needle_norm = f" {recipe_norm} "
        if needle_norm in haystack_norm:
            return 70
        if recipe_canon and pantry_canon:
            haystack_canon = f" {pantry_canon} "
            needle_canon = f" {recipe_canon} "
            if needle_canon in haystack_canon:
                return 65

    return 0


def _find_best_matching_pantry_key(pantry, recipe_ingredient):
    candidates = []
    for pantry_key in pantry.keys():
        score = _match_score(recipe_ingredient, pantry_key)
        if score > 0:
            # Prefer better score, then fewer extra words, then deterministic alpha order.
            recipe_word_count = len(normalize_ingredient(recipe_ingredient).split())
            pantry_word_count = len(normalize_ingredient(pantry_key).split())
            extra_words = max(0, pantry_word_count - recipe_word_count)
            candidates.append((score, -extra_words, pantry_key))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return candidates[0][2]


def get_exact_pantry_quantity_for_recipe_ingredient(pantry, recipe_ingredient):
    """
    Exact normalized-name lookup only.
    Example: pantry 'butter' must NOT satisfy recipe 'unsalted butter'.
    """
    normalized_recipe_ingredient = normalize_ingredient(recipe_ingredient)
    best_key = _find_best_matching_pantry_key(pantry, normalized_recipe_ingredient)
    if best_key is None:
        return None
    return pantry.get(best_key)


def can_make_recipe(pantry, recipe_requirements):
    missing = []
    insufficient = []

    for req_ing, req_qty in recipe_requirements.items():
        pantry_qty = get_exact_pantry_quantity_for_recipe_ingredient(pantry, req_ing)
        if pantry_qty is None:
            missing.append(req_ing)
            continue

        if not is_quantity_sufficient(pantry_qty, req_qty):
            shortage = compute_short_by(pantry_qty, req_qty)
            item = {'ingredient': req_ing, 'needed': req_qty, 'have': pantry_qty}
            if shortage is not None:
                item['short_by'] = shortage
            insufficient.append(item)

    can_make = len(missing) == 0 and len(insufficient) == 0
    return can_make, missing, insufficient


def suggest_recipes(pantry, recipes, min_score):
    """
    Returns a list of suggested recipes based on pantry contents.
    Includes partial match scoring and sort by best candidate first.
    """
    suggestions = []

    for recipe_name, requirements in recipes.items():
        can_make, missing, insufficient = can_make_recipe(pantry, requirements)
        total = len(requirements)
        full_matches = total - len(missing) - len(insufficient)
        score = full_matches / total if total > 0 else 0.0
        suggestion = {
            'recipe': recipe_name,
            'can_make': can_make,
            'missing': missing,
            'insufficient': insufficient,
            'score': score,
            'full_matches': full_matches,
            'total_ingredients': total
        }
        if suggestion["score"] >= min_score:
            suggestions.append(suggestion)

    # sort completed first, then high score, then fewest missing/insufficient
    suggestions.sort(key=lambda x: (not x['can_make'], -x['score'], len(x['missing']), len(x['insufficient'])))
    return suggestions

def print_suggestion(s):
    if s['can_make']:
        status = "ready to make"
    elif s['insufficient'] and not s['missing']:
        status = "ingredients present but insufficient"
    elif s['missing'] and not s['insufficient']:
        status = f"{s['score']*100:.0f}% matched"
    else:
        status = f"{s['score']*100:.0f}% matched (missing + insufficient)"

    print(f"- {s['recipe']} ({status})")
    if s['missing']:
        print(f"  Missing: {', '.join(s['missing'])}")
    if s['insufficient']:
        for i in s['insufficient']:
            short_by = i.get("short_by")
            if short_by is None:
                print(f"  Need more {i['ingredient']} ({i['needed']} required vs {i['have']} available)")
                continue
            amount = short_by["amount"]
            amount_txt = str(int(amount)) if float(amount).is_integer() else str(amount)
            unit = short_by.get("unit") or ""
            unit_txt = f" {unit}" if unit else ""
            mismatch_note = " (unit mismatch)" if short_by.get("unit_mismatch") else ""
            print(
                f"  Need {amount_txt}{unit_txt} more {i['ingredient']} ({i['needed']} required vs {i['have']} available){mismatch_note}"
            )


def display_suggestions_paginated(suggestions, min_match_score, batch_size):
    """
    Shows suggestions in batches. In interactive mode, user can request more.
    """
    if not suggestions:
        print(f"\nNo recipes found with at least {int(min_match_score * 100)}% ingredient match.")
        return

    total = len(suggestions)
    shown = 0
    interactive = sys.stdin.isatty()

    print(
        f"\nRecipe suggestions ({total} found, filtered to {int(min_match_score * 100)}%+ match):"
    )

    while shown < total:
        next_index = min(shown + batch_size, total)
        for s in suggestions[shown:next_index]:
            print_suggestion(s)
        shown = next_index

        if shown >= total:
            print("\nNo more recipe suggestions available.")
            return "done"

        if not interactive:
            return "done"

        user_choice = input(
            f"\nChoose next step ({shown}/{total} shown): [M]ore recipes, [A]dd ingredients, [E]dit ingredients, [Q]uit suggestions: "
        ).strip().lower()
        if user_choice in {"a", "add"}:
            return "add_ingredients"
        if user_choice in {"e", "edit"}:
            return "edit_ingredients"
        if user_choice in {"q", "quit", "n", "no"}:
            return "done"
        # Default to showing more for Enter or unrecognized input.

    return "done"
