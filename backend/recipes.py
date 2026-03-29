import sys
from ingredients import normalize_ingredient
from quantities import is_quantity_sufficient, compute_short_by

def can_make_recipe(pantry, recipe_requirements):
    missing = []
    insufficient = []

    for req_ing, req_qty in recipe_requirements.items():
        normalized = normalize_ingredient(req_ing)
        pantry_qty = pantry.get(normalized)
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