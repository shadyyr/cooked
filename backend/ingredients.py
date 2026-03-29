import re
from quantities import find_best_text_match
from gemini_utils import validate_ingredient_with_gemini

CURATED_COMMON_INGREDIENTS = {
    "salt", "pepper", "sugar", "flour", "rice", "pasta", "bread", "egg", "milk", "butter",
    "cheese", "tomato", "onion", "garlic", "potato", "chicken", "beef", "pork", "fish", "oil",
    "olive oil", "vegetable oil", "vinegar", "soy sauce", "lemon", "lime", "carrot",
    "broccoli", "mushroom", "spinach", "lettuce", "cucumber", "basil", "oregano", "thyme",
    "paprika", "cumin", "chili", "ginger", "bean", "lentil", "corn", "apple", "banana",
    "strawberry", "blueberry", "yogurt", "cream", "canned tomato", "avocado oil"
}

API_SEEN_INGREDIENTS = set()
INGREDIENT_FREQUENCY = {}

VALID_SCORE_THRESHOLD = 0.50
SUSPICIOUS_SCORE_THRESHOLD = 0.20

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

    # allow letters, digits, spaces, hyphens, apostrophes, and slash for ratio-style names
    if not re.fullmatch(r"[a-zA-Z0-9\s\-'/]+", ingredient):
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
    # Detect common path-like patterns, but allow ratio-like ingredient tokens (e.g. "95/5 beef")
    looks_like_windows_path = bool(re.match(r"^[a-zA-Z]:[\\/]", text))
    looks_like_unix_abs_path = text.startswith("/")
    looks_like_url = bool(re.match(r"^[a-zA-Z]+://", text))
    looks_like_relative_path = bool(re.search(r"[\\/]", text) and re.search(r"\.[a-zA-Z0-9]{1,5}$", text))
    if looks_like_windows_path or looks_like_unix_abs_path or looks_like_url or looks_like_relative_path:
        return False, "This looks like a file path, not an ingredient."
    if not re.fullmatch(r"[a-zA-Z0-9\s\-'/]+", lowered):
        return False, "Use letters, numbers, spaces, hyphens, apostrophes, or slash for ratios."
    return True, None

def get_ingredient_vocabulary(fallback_recipes):
    fallback_ingredients = set()
    for requirements in fallback_recipes.values():
        for ing in requirements.keys():
            fallback_ingredients.add(normalize_ingredient(ing))
    curated = {normalize_ingredient(x) for x in CURATED_COMMON_INGREDIENTS}
    api_seen = {normalize_ingredient(x) for x in API_SEEN_INGREDIENTS}
    observed = {normalize_ingredient(x) for x in INGREDIENT_FREQUENCY.keys()}
    return fallback_ingredients | curated | api_seen | observed


def get_fallback_ingredient_counts(fallback_recipes):
    counts = {}
    for requirements in fallback_recipes.values():
        for ing in requirements.keys():
            normalized = normalize_ingredient(ing)
            counts[normalized] = counts.get(normalized, 0) + 1
    return counts


def record_ingredient_observation(ingredient_text):
    normalized = normalize_ingredient(ingredient_text)
    INGREDIENT_FREQUENCY[normalized] = INGREDIENT_FREQUENCY.get(normalized, 0) + 1
    return INGREDIENT_FREQUENCY[normalized]

def suggest_ingredient_correction(ingredient_text, fallback_recipes):
    vocabulary = sorted(get_ingredient_vocabulary(fallback_recipes))
    return find_best_text_match(ingredient_text, vocabulary, max_dist_short=1, max_dist_long=2)


def get_api_hit_count_signal(normalized_ingredient):
    """
    Tries to use cached API info first, then a live hit count lookup.
    Returns None when unavailable.
    """
    try:
        # Local import avoids circular import at module load time.
        from api import get_api_hit_count_for_ingredient
        return get_api_hit_count_for_ingredient(normalized_ingredient)
    except Exception:
        return None


def compute_ingredient_confidence(normalized, fallback_recipes):
    fallback_counts = get_fallback_ingredient_counts(fallback_recipes)
    fallback_count = fallback_counts.get(normalized, 0)
    curated = normalized in {normalize_ingredient(x) for x in CURATED_COMMON_INGREDIENTS}
    api_seen = normalized in API_SEEN_INGREDIENTS
    observed_count = INGREDIENT_FREQUENCY.get(normalized, 0)
    api_hits = get_api_hit_count_signal(normalized)

    fallback_signal = min(fallback_count / 3.0, 1.0)
    observed_signal = min(observed_count / 5.0, 1.0)
    api_signal = min((api_hits or 0) / 10.0, 1.0) if api_hits is not None else 0.0

    score = 0.0
    if curated:
        score += 0.30
    score += 0.25 * fallback_signal
    if api_seen:
        score += 0.15
    score += 0.15 * observed_signal
    score += 0.15 * api_signal

    score = max(0.0, min(1.0, score))
    return score, {
        "curated": curated,
        "fallback_count": fallback_count,
        "api_seen": api_seen,
        "observed_count": observed_count,
        "api_hit_count": api_hits,
    }


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
    score, signals = compute_ingredient_confidence(normalized, fallback_recipes)
    suggestion = suggest_ingredient_correction(normalized, fallback_recipes)
    in_vocab = normalized in vocabulary

    curated_vocab = {normalize_ingredient(x) for x in CURATED_COMMON_INGREDIENTS}
    if normalized in curated_vocab:
        in_vocab = True
        score = max(score, VALID_SCORE_THRESHOLD + 0.1)

    # Heuristic for reasonable compound ingredients:
    # examples: "avocado oil", "garlic powder", "tomato sauce"
    tokens = [t for t in normalized.split() if t]
    if len(tokens) >= 2:
        head = tokens[-1]
        common_heads = {
            "oil", "powder", "sauce", "paste", "vinegar", "salt", "sugar", "flour",
            "milk", "cream", "butter", "cheese", "pepper", "juice", "stock", "broth",
        }
        if head in common_heads or head in vocabulary:
            in_vocab = True
            score = max(score, VALID_SCORE_THRESHOLD + 0.05)

    # Gemini assist for any non-confident ingredient:
    # - hard failures
    # - moderate/suspicious confidence cases
    if not (in_vocab and score >= VALID_SCORE_THRESHOLD):
        ai_check = validate_ingredient_with_gemini(normalized)
        if ai_check is not None:
            if ai_check.get("is_valid"):
                in_vocab = True
                score = max(score, VALID_SCORE_THRESHOLD + 0.05)
            else:
                ai_reason = ai_check.get("reason") or (
                    f"'{normalized}' is not recognized as a cooking ingredient."
                )
                return {
                    "status": "invalid",
                    "normalized": None,
                    "reason": ai_reason,
                    "suggestion": suggestion if suggestion != normalized else None,
                    "confidence_score": score,
                    "signals": signals,
                }

    if in_vocab and score >= VALID_SCORE_THRESHOLD:
        return {
            "status": "valid",
            "normalized": normalized,
            "reason": None,
            "suggestion": None,
            "confidence_score": score,
            "signals": signals,
        }

    if score < SUSPICIOUS_SCORE_THRESHOLD and not in_vocab:
        reason = (
            f"Low confidence ingredient ({score:.2f}). It does not appear in curated, fallback, "
            "or API-observed ingredient vocab."
        )
    else:
        reason = (
            f"Ingredient looks syntactically valid but has moderate confidence ({score:.2f}) "
            "in known ingredient behavior."
        )

    return {
        "status": "suspicious",
        "normalized": normalized,
        "reason": reason,
        "suggestion": suggestion if suggestion != normalized else None,
        "confidence_score": score,
        "signals": signals,
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
        confidence = assessment.get("confidence_score")
        if suggestion:
            if confidence is None:
                print(f"'{ingredient}' looks uncommon. Did you mean '{suggestion}'?")
            else:
                print(
                    f"'{ingredient}' looks uncommon (confidence {confidence:.2f}). "
                    f"Did you mean '{suggestion}'?"
                )
            choice = input("[Y]es use suggestion, [K]eep as entered, [R]e-enter: ").strip().lower()
            if choice in {"y", "yes"}:
                return suggestion, "suspicious"
            if choice in {"k", "keep"}:
                return assessment["normalized"], "suspicious"
            ingredient = input(f"{prompt_label}: ").strip().lower()
            if ingredient == "done":
                return "done", "done"
            continue

        if confidence is None:
            print(f"'{ingredient}' looks uncommon. {assessment['reason']}")
        else:
            print(f"'{ingredient}' looks uncommon (confidence {confidence:.2f}). {assessment['reason']}")
        choice = input("[K]eep as entered or [R]e-enter: ").strip().lower()
        if choice in {"k", "keep", "y", "yes"}:
            return assessment["normalized"], "suspicious"
        ingredient = input(f"{prompt_label}: ").strip().lower()
        if ingredient == "done":
            return "done", "done"


def validate_ingredient_for_api(raw_ingredient, fallback_recipes):
    """
    Strict validation for API requests:
    - uses existing layered logic first
    - if uncertain (suspicious), asks Gemini as final judge
    """
    assessment = assess_ingredient_confidence(raw_ingredient, fallback_recipes)
    status = assessment.get("status")

    if status == "valid":
        return {
            "valid": True,
            "normalized": assessment.get("normalized"),
            "reason": None,
            "suggestion": None,
            "confidence_score": assessment.get("confidence_score"),
        }

    if status == "invalid":
        return {
            "valid": False,
            "normalized": None,
            "reason": assessment.get("reason") or "Input is not a valid ingredient.",
            "suggestion": assessment.get("suggestion"),
            "confidence_score": assessment.get("confidence_score"),
        }

    # Suspicious path -> Gemini fallback
    normalized = assessment.get("normalized") or normalize_ingredient(raw_ingredient)
    ai_check = validate_ingredient_with_gemini(normalized)
    if ai_check is not None:
        if ai_check.get("is_valid"):
            return {
                "valid": True,
                "normalized": normalized,
                "reason": None,
                "suggestion": None,
                "confidence_score": 0.45,
            }
        ai_reason = ai_check.get("reason") or "Gemini did not recognize this as a cooking ingredient."
        return {
            "valid": False,
            "normalized": None,
            "reason": ai_reason,
            "suggestion": assessment.get("suggestion"),
            "confidence_score": assessment.get("confidence_score"),
        }

    # Gemini unavailable: reject uncertain input rather than silently accepting non-ingredients.
    return {
        "valid": False,
        "normalized": None,
        "reason": (
            assessment.get("reason")
            or "Ingredient could not be confidently validated."
        ),
        "suggestion": assessment.get("suggestion"),
        "confidence_score": assessment.get("confidence_score"),
    }
