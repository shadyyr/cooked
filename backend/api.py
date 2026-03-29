import json
from urllib import parse, request
from urllib.error import URLError, HTTPError
from ingredients import normalize_ingredient, API_SEEN_INGREDIENTS
from config import REQUEST_TIMEOUT, USER_AGENT

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
_RESPONSE_CACHE = {}
_INGREDIENT_CACHE = {}
_MEAL_METADATA_BY_NAME = {}

def mealdb_get_json(url):
    if url in _RESPONSE_CACHE:
        return _RESPONSE_CACHE[url]

    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = resp.read().decode("utf-8")
        parsed = json.loads(data)
        _RESPONSE_CACHE[url] = parsed
        return parsed
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"[API ERROR] Failed request for URL: {url}")
        print(f"[API ERROR] {type(e).__name__}: {e}")
        raise

def search_meal_ids_by_ingredient(ingredient):
    normalized = normalize_ingredient(ingredient)

    # ingredient-level cache check
    if normalized in _INGREDIENT_CACHE:
        return _INGREDIENT_CACHE[normalized]

    encoded = parse.quote(normalized)
    url = f"{MEALDB_BASE_URL}/filter.php?i={encoded}"

    payload = mealdb_get_json(url)
    meals = payload.get("meals") or []
    ids = {m["idMeal"] for m in meals if m.get("idMeal")}

    # store in cache
    _INGREDIENT_CACHE[normalized] = ids

    return ids


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


def extract_meal_metadata(meal):
    meal_name = (meal.get("strMeal") or "").strip()
    if not meal_name:
        return None, None

    instructions_raw = (meal.get("strInstructions") or "").strip()
    instructions = [
        line.strip()
        for line in instructions_raw.splitlines()
        if line and line.strip()
    ]
    description = instructions_raw.split(".")[0].strip() if instructions_raw else ""
    if description:
        description = f"{description}."

    metadata = {
        "image_url": (meal.get("strMealThumb") or "").strip() or None,
        "description": description or None,
        "instructions": instructions,
        "tags": [t.strip() for t in (meal.get("strTags") or "").split(",") if t.strip()],
        "category": (meal.get("strCategory") or "").strip() or None,
        "area": (meal.get("strArea") or "").strip() or None,
        "source_url": (meal.get("strSource") or "").strip() or None,
        "youtube_url": (meal.get("strYoutube") or "").strip() or None,
    }
    return meal_name, metadata


def fetch_mealdb_recipes(pantry, limit):
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
            metadata_name, metadata = extract_meal_metadata(meal)
            if metadata_name and metadata:
                _MEAL_METADATA_BY_NAME[metadata_name] = metadata

    return recipes


def get_api_hit_count_for_ingredient(ingredient):
    """
    Returns number of MealDB hits for an ingredient.
    Uses cache when available and falls back to a live lookup.
    """
    normalized = normalize_ingredient(ingredient)
    if normalized in _INGREDIENT_CACHE:
        return len(_INGREDIENT_CACHE[normalized])
    return None


def get_meal_metadata_by_name(recipe_name):
    return _MEAL_METADATA_BY_NAME.get(recipe_name)
