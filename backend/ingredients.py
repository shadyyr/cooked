import re
from quantities import find_best_text_match

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

def get_ingredient_vocabulary(fallback_recipes):
    fallback_ingredients = set()
    for requirements in fallback_recipes.values():
        for ing in requirements.keys():
            fallback_ingredients.add(normalize_ingredient(ing))
    curated = {normalize_ingredient(x) for x in CURATED_COMMON_INGREDIENTS}
    api_seen = {normalize_ingredient(x) for x in API_SEEN_INGREDIENTS}
    return fallback_ingredients | curated | api_seen

def suggest_ingredient_correction(ingredient_text, fallback_recipes):
    vocabulary = sorted(get_ingredient_vocabulary(fallback_recipes))
    return find_best_text_match(ingredient_text, vocabulary, max_dist_short=1, max_dist_long=2)


def assess_ingredient_confidence(ingredient_text, fallback_recipes):
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
    vocabulary = get_ingredient_vocabulary(fallback_recipes)
    if normalized in vocabulary:
        return {
            "status": "valid",
            "normalized": normalized,
            "reason": None,
            "suggestion": None,
        }

    suggestion = suggest_ingredient_correction(normalized, fallback_recipes)
    return {
        "status": "suspicious",
        "normalized": normalized,
        "reason": "Ingredient looks syntactically valid but is uncommon in known recipes.",
        "suggestion": suggestion if suggestion != normalized else None,
    }


def resolve_ingredient_input_with_guidance(raw_ingredient, fallback_recipes, prompt_label="Ingredient"):
    """
    Interactive resolver for ingredient confidence:
    - invalid -> re-enter
    - suspicious -> keep, use suggestion, or re-enter
    """
    ingredient = raw_ingredient
    while True:
        assessment = assess_ingredient_confidence(ingredient, fallback_recipes)
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
