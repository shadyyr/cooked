import json
import re
import sys
import difflib
from urllib import parse, request
from urllib.error import URLError, HTTPError


MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
API_RESULT_LIMIT = 12
DISPLAY_BATCH_SIZE = 3
MIN_MATCH_SCORE = 0.30

CURATED_COMMON_INGREDIENTS = {
    "salt", "pepper", "sugar", "flour", "rice", "pasta", "bread", "egg", "milk", "butter",
    "cheese", "tomato", "onion", "garlic", "potato", "chicken", "beef", "pork", "fish",
    "olive oil", "vegetable oil", "vinegar", "soy sauce", "lemon", "lime", "carrot",
    "broccoli", "mushroom", "spinach", "lettuce", "cucumber", "basil", "oregano", "thyme",
    "paprika", "cumin", "chili", "ginger", "bean", "lentil", "corn", "apple", "banana",
    "strawberry", "blueberry", "yogurt", "cream", "canned tomato"
}

API_SEEN_INGREDIENTS = set()

# Mapping for plural to singular forms
PLURAL_MAP = {
    "eggs": "egg",
    "tomatoes": "tomato",
    "onions": "onion",
    "potatoes": "potato",
    "carrots": "carrot",
    "apples": "apple",
    "bananas": "banana",
    "oranges": "orange",
    "strawberries": "strawberry",
    "blueberries": "blueberry",
    "nuts": "nut",
    "seeds": "seed",
    "herbs": "herb",
    "spices": "spice",
    "oats": "oat",
    "cornflakes": "cornflake",
    "bread crumbs": "bread crumb",
    "crackers": "cracker",
    "frozen vegetables": "frozen vegetable",
    "canned tomatoes": "canned tomato",
    "canned beans": "canned bean",
    "lentils": "lentil",
    "peas": "pea",
    "green beans": "green bean",
    "mushrooms": "mushroom",
    "bell peppers": "bell pepper",
    "jalapenos": "jalapeno",
    "chilies": "chili",
    "sprinkles": "sprinkle",
    "extracts": "extract",
    "flavorings": "flavoring"
}

def normalize_ingredient(ingredient):
    """
    Normalizes an ingredient to its singular form using a mapping.
    """
    ingredient = ingredient.strip().lower()
    return PLURAL_MAP.get(ingredient, ingredient)

def is_valid_ingredient(ingredient):
    """
    Layer 1 syntax/sanity validation only.
    """
    ingredient = ingredient.strip().lower()

    if not ingredient:
        return False

    if len(ingredient) > 40:
        return False

    if not re.search(r"[a-zA-Z]", ingredient):
        return False

    # allow letters, spaces, hyphens, apostrophes
    if not re.fullmatch(r"[a-zA-Z\s\-']+", ingredient):
        return False

    return True


def ingredient_syntax_reason(ingredient):
    text = ingredient.strip()
    lowered = text.lower()
    if not lowered:
        return False, "Ingredient cannot be empty."
    if len(lowered) > 40:
        return False, "Ingredient is too long. Keep it under 40 characters."
    if not re.search(r"[a-zA-Z]", lowered):
        return False, "Ingredient must contain letters."
    if "\\" in text or "/" in text or ":" in text:
        return False, "This looks like a file path, not an ingredient."
    if not re.fullmatch(r"[a-zA-Z\s\-']+", lowered):
        return False, "Use only letters, spaces, hyphens, or apostrophes."
    return True, None

def parse_quantity(quantity_input):
    """
    Accepts quantity input as text and returns sanitized quantity string.
    """
    return quantity_input.strip()


UNIT_MAP = {
    "cups": "cup",
    "cup": "cup",
    "tablespoons": "tbsp",
    "tablespoon": "tbsp",
    "tbsp": "tbsp",
    "teaspoons": "tsp",
    "teaspoon": "tsp",
    "tsp": "tsp",
    "grams": "g",
    "gram": "g",
    "g": "g",
    "kilograms": "kg",
    "kilogram": "kg",
    "kg": "kg",
    "ounces": "oz",
    "ounce": "oz",
    "oz": "oz",
    "pounds": "lb",
    "pound": "lb",
    "lbs": "lb",
    "lb": "lb",
    "milliliters": "ml",
    "milliliter": "ml",
    "ml": "ml",
    "liters": "l",
    "liter": "l",
    "l": "l",
    "cloves": "clove",
    "clove": "clove",
    "slice": "slice",
    "slices": "slice",
    "stick": "stick",
    "sticks": "stick",
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "can": "can",
    "cans": "can"
}

UNIT_CONVERSIONS_TO_BASE = {
    "ml": ("volume", 1.0),
    "tsp": ("volume", 5.0),
    "tbsp": ("volume", 15.0),
    "cup": ("volume", 240.0),
    "l": ("volume", 1000.0),
    "g": ("weight", 1.0),
    "kg": ("weight", 1000.0),
    "oz": ("weight", 28.3495),
    "lb": ("weight", 453.592),
    "slice": ("count", 1.0),
    "clove": ("count", 1.0),
    "stick": ("count", 1.0),
    "piece": ("count", 1.0),
    "can": ("count", 1.0),
}


def format_amount_unit(amount, unit):
    if float(amount).is_integer():
        amount_text = str(int(amount))
    else:
        amount_text = f"{float(amount):.2f}".rstrip("0").rstrip(".")
    if unit:
        return f"{amount_text} {unit}"
    return amount_text


def format_quantity_display(quantity_input):
    amount, unit = parse_amount_unit(quantity_input)
    if amount is None:
        return str(quantity_input).strip()
    return format_amount_unit(amount, unit)


def list_valid_units_text():
    units = sorted(set(UNIT_MAP.values()))
    return ", ".join(units)


def damerau_levenshtein(a, b):
    da = {}
    maxdist = len(a) + len(b)
    d = [[0] * (len(b) + 2) for _ in range(len(a) + 2)]
    d[0][0] = maxdist

    for i in range(len(a) + 1):
        d[i + 1][0] = maxdist
        d[i + 1][1] = i
    for j in range(len(b) + 1):
        d[0][j + 1] = maxdist
        d[1][j + 1] = j

    for i in range(1, len(a) + 1):
        db = 0
        for j in range(1, len(b) + 1):
            i1 = da.get(b[j - 1], 0)
            j1 = db
            cost = 0 if a[i - 1] == b[j - 1] else 1
            if cost == 0:
                db = j
            d[i + 1][j + 1] = min(
                d[i][j] + cost,
                d[i + 1][j] + 1,
                d[i][j + 1] + 1,
                d[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1)
            )
        da[a[i - 1]] = i

    return d[len(a) + 1][len(b) + 1]


def find_best_text_match(query_text, candidates, max_dist_short=1, max_dist_long=2):
    if not query_text:
        return None
    query = query_text.lower().strip()
    best = None
    for candidate in candidates:
        cand = candidate.lower().strip()
        dist = damerau_levenshtein(query, cand)
        ratio = difflib.SequenceMatcher(a=query, b=cand).ratio()
        length_gap = abs(len(query) - len(cand))
        rank = (dist, length_gap, -ratio, cand)
        if best is None or rank < best[0]:
            best = (rank, cand)

    if best is None:
        return None

    best_rank, best_candidate = best
    best_dist = best_rank[0]
    max_allowed_dist = max_dist_short if len(query) <= 3 else max_dist_long
    if best_dist > max_allowed_dist:
        return None
    return best_candidate


def get_ingredient_vocabulary():
    fallback_ingredients = set()
    for requirements in FALLBACK_RECIPES.values():
        for ing in requirements.keys():
            fallback_ingredients.add(normalize_ingredient(ing))
    curated = {normalize_ingredient(x) for x in CURATED_COMMON_INGREDIENTS}
    api_seen = {normalize_ingredient(x) for x in API_SEEN_INGREDIENTS}
    return fallback_ingredients | curated | api_seen


def suggest_unit_correction(unit_text):
    candidate_units = sorted(set(UNIT_MAP.values()))
    return find_best_text_match(unit_text, candidate_units)


def suggest_ingredient_correction(ingredient_text):
    vocabulary = sorted(get_ingredient_vocabulary())
    return find_best_text_match(ingredient_text, vocabulary, max_dist_short=1, max_dist_long=2)


def assess_ingredient_confidence(ingredient_text):
    """
    Layer 1: syntax/sanity
    Layer 2: normalization/structuring
    Layer 3: behavioral confidence from known vocabulary
    """
    syntax_ok, syntax_reason = ingredient_syntax_reason(ingredient_text)
    if not syntax_ok:
        return {
            "status": "invalid",
            "normalized": None,
            "reason": syntax_reason,
            "suggestion": None,
        }

    normalized = normalize_ingredient(ingredient_text)
    vocabulary = get_ingredient_vocabulary()
    if normalized in vocabulary:
        return {
            "status": "valid",
            "normalized": normalized,
            "reason": None,
            "suggestion": None,
        }

    suggestion = suggest_ingredient_correction(normalized)
    return {
        "status": "suspicious",
        "normalized": normalized,
        "reason": "Ingredient looks syntactically valid but is uncommon in known recipes.",
        "suggestion": suggestion if suggestion != normalized else None,
    }


def resolve_ingredient_input_with_guidance(raw_ingredient, prompt_label="Ingredient"):
    """
    Interactive resolver for ingredient confidence:
    - invalid -> re-enter
    - suspicious -> keep, use suggestion, or re-enter
    """
    ingredient = raw_ingredient
    while True:
        assessment = assess_ingredient_confidence(ingredient)
        status = assessment["status"]
        if status == "valid":
            return assessment["normalized"], "valid"

        if status == "invalid":
            print(f"Invalid ingredient '{ingredient}'. {assessment['reason']}")
            ingredient = input(f"{prompt_label}: ").strip().lower()
            if ingredient == "done":
                return "done", "done"
            continue

        suggestion = assessment["suggestion"]
        if suggestion:
            print(f"'{ingredient}' looks uncommon. Did you mean '{suggestion}'?")
            choice = input("[Y]es use suggestion, [K]eep as entered, [R]e-enter: ").strip().lower()
            if choice in {"y", "yes"}:
                return suggestion, "suspicious"
            if choice in {"k", "keep"}:
                return assessment["normalized"], "suspicious"
            ingredient = input(f"{prompt_label}: ").strip().lower()
            if ingredient == "done":
                return "done", "done"
            continue

        print(f"'{ingredient}' looks uncommon. {assessment['reason']}")
        choice = input("[K]eep as entered or [R]e-enter: ").strip().lower()
        if choice in {"k", "keep", "y", "yes"}:
            return assessment["normalized"], "suspicious"
        ingredient = input(f"{prompt_label}: ").strip().lower()
        if ingredient == "done":
            return "done", "done"


def validate_quantity_input(quantity_input):
    """
    Validates quantity format and unit.
    Quantity must start with a number (supports fractions), followed by optional valid unit.
    """
    amount, unit = parse_amount_unit(quantity_input)
    if amount is None:
        return False, "Invalid quantity format. Use something like '2 cup', '250 ml', '1/2 tbsp', or '3'."

    if unit and unit not in set(UNIT_MAP.values()):
        suggestion = suggest_unit_correction(unit)
        if suggestion:
            return False, f"Invalid unit '{unit}'. Did you mean '{suggestion}'?"
        return False, f"Invalid unit '{unit}'."

    return True, None


def convert_amount_between_units(amount, from_unit, to_unit):
    if from_unit == to_unit:
        return amount
    if from_unit not in UNIT_CONVERSIONS_TO_BASE or to_unit not in UNIT_CONVERSIONS_TO_BASE:
        return None

    from_dim, from_factor = UNIT_CONVERSIONS_TO_BASE[from_unit]
    to_dim, to_factor = UNIT_CONVERSIONS_TO_BASE[to_unit]
    if from_dim != to_dim:
        return None
    if from_dim == "count":
        # Do not convert different count-like units (e.g., clove -> slice).
        return None

    amount_in_base = amount * from_factor
    return amount_in_base / to_factor


def combine_quantities(existing_quantity, additional_quantity):
    """
    Combine two quantity strings cumulatively.
    Keeps the existing unit as the display/storage unit when possible.
    """
    existing_amt, existing_unit = parse_amount_unit(existing_quantity)
    additional_amt, additional_unit = parse_amount_unit(additional_quantity)

    if existing_amt is None or additional_amt is None:
        return None, None

    # If existing has no unit, use the new unit (if any) as canonical.
    target_unit = existing_unit or additional_unit
    normalized_additional = additional_amt

    if target_unit:
        from_unit = additional_unit or target_unit
        normalized_additional = convert_amount_between_units(additional_amt, from_unit, target_unit)
        if normalized_additional is None:
            return None, None

    combined = existing_amt + normalized_additional
    return format_amount_unit(combined, target_unit), target_unit


def parse_amount_unit(quantity_input):
    """
    Parse quantity string into (amount, unit).
    Example: '2 eggs' -> (2.0, 'egg'), '1 cup milk' -> (1.0, 'cup'), '250ml' -> (250.0, 'ml').
    Returns (None, None) when parsing is not possible.
    """
    q = str(quantity_input).strip().lower()
    if not q:
        return None, None

    # Keep only first quantity chunk (e.g. "1-2 tbsp" -> "1 tbsp").
    q = q.replace("-", " ")

    # number plus optional unit text; trailing words ignored
    pattern = r'^\s*(?P<num>\d+(?:\.\d+)?(?:/\d+)?)(?:\s*(?P<unit>[a-zA-Z]+))?.*$'
    m = re.match(pattern, q)
    if not m:
        return None, None

    num_text = m.group('num')
    unit = (m.group('unit') or '').lower()

    # unit normalization with map
    unit = UNIT_MAP.get(unit, unit)

    # convert fractional numbers to float
    if '/' in num_text:
        n, d = num_text.split('/')
        try:
            amount = float(n) / float(d)
        except (ValueError, ZeroDivisionError):
            return None, None
    else:
        try:
            amount = float(num_text)
        except ValueError:
            return None, None

    return amount, unit


def is_quantity_sufficient(pantry_quantity, required_quantity):
    pantry_amt, pantry_unit = parse_amount_unit(pantry_quantity)
    required_amt, required_unit = parse_amount_unit(required_quantity)

    if required_amt is None:
        return pantry_quantity.strip() != ''

    if pantry_amt is None:
        return True

    # Try conversion if units differ
    if pantry_unit and required_unit and pantry_unit != required_unit:
        converted = convert_amount_between_units(pantry_amt, pantry_unit, required_unit)
        if converted is not None:
            return converted >= required_amt

    return pantry_amt >= required_amt


def compute_short_by(pantry_quantity, required_quantity):
    pantry_amt, pantry_unit = parse_amount_unit(pantry_quantity)
    required_amt, required_unit = parse_amount_unit(required_quantity)

    if pantry_amt is None or required_amt is None:
        return None

    # Try conversion first
    if pantry_unit and required_unit and pantry_unit != required_unit:
        converted = convert_amount_between_units(pantry_amt, pantry_unit, required_unit)
        if converted is not None:
            short_amt = max(0.0, required_amt - converted)
            if short_amt <= 0:
                return None
            return {"amount": round(short_amt, 3), "unit": required_unit, "unit_mismatch": False}

    # fallback
    short_amt = max(0.0, required_amt - pantry_amt)
    if short_amt <= 0:
        return None

    return {"amount": round(short_amt, 3), "unit": required_unit or pantry_unit, "unit_mismatch": True}


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


def suggest_recipes(pantry, recipes, min_score=MIN_MATCH_SCORE):
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


def display_suggestions_paginated(suggestions, batch_size=DISPLAY_BATCH_SIZE):
    """
    Shows suggestions in batches. In interactive mode, user can request more.
    """
    if not suggestions:
        print(f"\nNo recipes found with at least {int(MIN_MATCH_SCORE * 100)}% ingredient match.")
        return

    total = len(suggestions)
    shown = 0
    interactive = sys.stdin.isatty()

    print(
        f"\nRecipe suggestions ({total} found, filtered to {int(MIN_MATCH_SCORE * 100)}%+ match):"
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
            normalized, confidence = resolve_ingredient_input_with_guidance(ingredient, prompt_label="Ingredient")
            if normalized == "done":
                break
            if confidence == "suspicious":
                print(f"Accepted uncommon ingredient: {normalized}")
        else:
            assessment = assess_ingredient_confidence(ingredient)
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
        next_action = display_suggestions_paginated(suggestions, batch_size=DISPLAY_BATCH_SIZE)

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
