import json
import os
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, make_response, request

from api import fetch_mealdb_recipes, get_meal_metadata_by_name
from config import API_RESULT_LIMIT, MIN_MATCH_SCORE
from fallbacks import FALLBACK_RECIPES
from ingredients import normalize_ingredient, validate_ingredient_for_api
from quantities import combine_quantities, validate_unit_for_ingredient, suggest_units_for_ingredient
from recipes import suggest_recipes


app = Flask(__name__)

_RECIPE_DETAIL_CACHE = {}
RECIPE_META_KEYS = {"image_url", "youtube_url", "description", "instructions"}


def slugify_recipe_name(name):
    slug = name.lower()
    slug = "".join(ch if ch.isalnum() or ch == " " else "" for ch in slug)
    return "-".join(slug.split())


def with_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp


@app.after_request
def add_cors_headers(resp):
    return with_cors(resp)


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        return with_cors(make_response("", 204))
    return jsonify({"status": "ok"})


def parse_pantry_from_payload(payload):
    """
    Accepts:
    - ingredients: ["egg", "milk"]
    - ingredients: [{"ingredient": "egg", "quantity": "2", "unit": "count"}, ...]
    """
    ingredients = payload.get("ingredients") or []
    pantry = {}
    invalid_ingredients = []

    for item in ingredients:
        if isinstance(item, str):
            raw_name = str(item).strip()
            if not raw_name:
                continue
            validation = validate_ingredient_for_api(raw_name, FALLBACK_RECIPES)
            if not validation.get("valid"):
                invalid_ingredients.append(
                    {
                        "ingredient": raw_name,
                        "reason": validation.get("reason"),
                        "suggestion": validation.get("suggestion"),
                    }
                )
                continue
            name = validation.get("normalized") or normalize_ingredient(raw_name)
            qty = "1 piece"
        elif isinstance(item, dict):
            raw_name = str(item.get("ingredient", "")).strip()
            if not raw_name:
                continue
            validation = validate_ingredient_for_api(raw_name, FALLBACK_RECIPES)
            if not validation.get("valid"):
                invalid_ingredients.append(
                    {
                        "ingredient": raw_name,
                        "reason": validation.get("reason"),
                        "suggestion": validation.get("suggestion"),
                    }
                )
                continue
            name = validation.get("normalized") or normalize_ingredient(raw_name)
            raw_qty = str(item.get("quantity", "")).strip()
            raw_unit = str(item.get("unit", "")).strip()
            if raw_unit:
                unit_valid, unit_reason, unit_suggestion = validate_unit_for_ingredient(raw_name, raw_unit)
                if not unit_valid:
                    invalid_ingredients.append(
                        {
                            "ingredient": raw_name,
                            "reason": unit_reason,
                            "suggestion": unit_suggestion,
                        }
                    )
                    continue
            if raw_qty:
                qty = f"{raw_qty} {raw_unit}".strip()
            else:
                qty = "1 piece"
        else:
            continue

        if not name:
            continue

        if name in pantry:
            merged, _ = combine_quantities(pantry[name], qty)
            pantry[name] = merged if merged is not None else pantry[name]
        else:
            pantry[name] = qty

    return pantry, invalid_ingredients


def split_recipe_requirements_and_meta(recipe_data):
    """
    Supports fallback recipes that may include metadata keys mixed into ingredient maps.
    """
    requirements = {}
    meta = {}
    for key, value in (recipe_data or {}).items():
        if key in RECIPE_META_KEYS:
            meta[key] = value
        else:
            requirements[key] = value
    return requirements, meta


def serialize_recipe(recipe_name, requirements, suggestion, source):
    requirements, fallback_meta = split_recipe_requirements_and_meta(requirements)
    meal_meta = get_meal_metadata_by_name(recipe_name) if source == "themealdb" else None
    merged_meta = {}
    merged_meta.update(fallback_meta or {})
    merged_meta.update(meal_meta or {})
    instructions = merged_meta.get("instructions", [])
    if isinstance(instructions, str):
        instructions = [line.strip() for line in instructions.splitlines() if line.strip()]
    description = (
        merged_meta.get("description")
        or (instructions[0] if instructions else f"A recipe for {recipe_name}.")
    )
    recipe_id = slugify_recipe_name(recipe_name)
    missing_names = suggestion.get("missing", [])
    missing_details = []
    for ing in missing_names:
        normalized_ing = normalize_ingredient(ing)
        needed_qty = requirements.get(normalized_ing, requirements.get(ing, "unknown"))
        missing_details.append({"ingredient": ing, "needed": needed_qty})

    payload = {
        "id": recipe_id,
        "recipe_name": recipe_name,
        "description": description,
        "ingredients": requirements,
        "instructions": instructions,
        "image_url": merged_meta.get("image_url"),
        "youtube_url": merged_meta.get("youtube_url"),
        "score": suggestion.get("score"),
        "match_percent": round((suggestion.get("score") or 0.0) * 100, 1),
        "source": source,
        "can_make": suggestion.get("can_make"),
        "missing": missing_names,
        "missing_details": missing_details,
        "insufficient": suggestion.get("insufficient", []),
    }
    _RECIPE_DETAIL_CACHE[recipe_id] = payload
    return payload


@app.route("/api/recipes/search", methods=["POST", "OPTIONS"])
def search_recipes():
    if request.method == "OPTIONS":
        return with_cors(make_response("", 204))

    payload = request.get_json(silent=True) or {}
    limit_raw = payload.get("limit")
    limit = API_RESULT_LIMIT if limit_raw is None else limit_raw
    try:
        limit = max(1, min(int(limit), 50))
    except (TypeError, ValueError):
        limit = API_RESULT_LIMIT

    min_score_raw = payload.get("min_match_score", MIN_MATCH_SCORE)
    try:
        min_score = max(0.0, min(float(min_score_raw), 1.0))
    except (TypeError, ValueError):
        min_score = MIN_MATCH_SCORE

    pantry, invalid_ingredients = parse_pantry_from_payload(payload)
    if invalid_ingredients:
        return (
            jsonify(
                {
                    "error": "invalid_ingredient_input",
                    "message": "One or more inputs are not valid ingredients.",
                    "invalid_ingredients": invalid_ingredients,
                }
            ),
            400,
        )
    if not pantry:
        fallback_limit = len(FALLBACK_RECIPES) if limit_raw is None else limit
        fallback_names = list(FALLBACK_RECIPES.keys())[:fallback_limit]
        suggestions = [
            {
                "recipe": name,
                "score": 0.0,
                "can_make": False,
                "missing": list(split_recipe_requirements_and_meta(FALLBACK_RECIPES[name])[0].keys()),
                "insufficient": [],
            }
            for name in fallback_names
        ]
        recipes = [
            serialize_recipe(name, FALLBACK_RECIPES[name], s, "fallback")
            for name, s in zip(fallback_names, suggestions)
        ]
        return jsonify(
            {
                "recipes": recipes,
                "source": "fallback",
                "count": len(recipes),
                "filters": {"min_match_score": min_score},
                "debug": {"api_recipe_count": 0, "pantry_count": 0},
            }
        )

    api_error = None
    try:
        api_recipes = fetch_mealdb_recipes(pantry, limit=limit)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as e:
        api_recipes = {}
        api_error = f"{type(e).__name__}: {e}"

    recipes_to_use = api_recipes if api_recipes else FALLBACK_RECIPES
    source = "themealdb" if api_recipes else "fallback"

    suggestions = suggest_recipes(pantry, recipes_to_use, min_score=min_score)
    # When user provided ingredients, hide exact 0% matches.
    suggestions = [s for s in suggestions if (s.get("score") or 0.0) > 0.0]
    suggestions = suggestions[:limit]
    recipe_payload = []
    for suggestion in suggestions:
        recipe_name = suggestion["recipe"]
        requirements = recipes_to_use.get(recipe_name, {})
        recipe_payload.append(serialize_recipe(recipe_name, requirements, suggestion, source))

    return jsonify(
        {
            "recipes": recipe_payload,
            "source": source,
            "count": len(recipe_payload),
            "filters": {"min_match_score": min_score},
            "debug": {
                "api_recipe_count": len(api_recipes),
                "pantry_count": len(pantry),
                "api_error": api_error,
            },
        }
    )


@app.route("/api/ingredients/validate", methods=["POST", "OPTIONS"])
def validate_ingredient():
    if request.method == "OPTIONS":
        return with_cors(make_response("", 204))

    payload = request.get_json(silent=True) or {}
    raw_ingredient = str(payload.get("ingredient", "")).strip()
    if not raw_ingredient:
        return (
            jsonify(
                {
                    "valid": False,
                    "reason": "Ingredient cannot be empty.",
                    "suggestion": None,
                }
            ),
            400,
        )

    result = validate_ingredient_for_api(raw_ingredient, FALLBACK_RECIPES)
    if result.get("valid"):
        return jsonify(
            {
                "valid": True,
                "normalized": result.get("normalized"),
                "reason": None,
                "suggestion": None,
            }
        )

    return (
        jsonify(
            {
                "valid": False,
                "reason": result.get("reason"),
                "suggestion": result.get("suggestion"),
            }
        ),
        400,
    )


@app.route("/api/ingredients/validate-entry", methods=["POST", "OPTIONS"])
def validate_ingredient_entry():
    if request.method == "OPTIONS":
        return with_cors(make_response("", 204))

    payload = request.get_json(silent=True) or {}
    raw_ingredient = str(payload.get("ingredient", "")).strip()
    raw_unit = str(payload.get("unit", "")).strip()
    if not raw_ingredient:
        return (
            jsonify(
                {
                    "valid": False,
                    "reason": "Ingredient cannot be empty.",
                    "suggestion": None,
                }
            ),
            400,
        )

    ingredient_result = validate_ingredient_for_api(raw_ingredient, FALLBACK_RECIPES)
    if not ingredient_result.get("valid"):
        return (
            jsonify(
                {
                    "valid": False,
                    "reason": ingredient_result.get("reason"),
                    "suggestion": ingredient_result.get("suggestion"),
                }
            ),
            400,
        )

    if raw_unit:
        unit_valid, unit_reason, unit_suggestion = validate_unit_for_ingredient(raw_ingredient, raw_unit)
        if not unit_valid:
            return (
                jsonify(
                    {
                        "valid": False,
                        "reason": unit_reason,
                        "suggestion": unit_suggestion,
                    }
                ),
                400,
            )

    return jsonify(
        {
            "valid": True,
            "normalized": ingredient_result.get("normalized"),
            "reason": None,
            "suggestion": None,
        }
    )


@app.route("/api/ingredients/suggest-units", methods=["POST", "OPTIONS"])
def suggest_units():
    if request.method == "OPTIONS":
        return with_cors(make_response("", 204))

    payload = request.get_json(silent=True) or {}
    raw_ingredient = str(payload.get("ingredient", "")).strip()
    if not raw_ingredient:
        return jsonify({"units": []})

    units = suggest_units_for_ingredient(raw_ingredient)
    return jsonify({"units": units})


@app.route("/api/recipes/<recipe_id>", methods=["GET", "OPTIONS"])
def get_recipe(recipe_id):
    if request.method == "OPTIONS":
        return with_cors(make_response("", 204))

    if recipe_id in _RECIPE_DETAIL_CACHE:
        return jsonify(_RECIPE_DETAIL_CACHE[recipe_id])

    for name, requirements in FALLBACK_RECIPES.items():
        if slugify_recipe_name(name) == recipe_id:
            clean_requirements, fallback_meta = split_recipe_requirements_and_meta(requirements)
            payload = {
                "id": recipe_id,
                "recipe_name": name,
                "description": fallback_meta.get("description", f"A recipe for {name}."),
                "ingredients": clean_requirements,
                "instructions": fallback_meta.get("instructions", []),
                "image_url": fallback_meta.get("image_url"),
                "youtube_url": fallback_meta.get("youtube_url"),
                "score": 0.0,
                "match_percent": 0.0,
                "source": "fallback",
                "can_make": False,
                "missing": list(clean_requirements.keys()),
                "insufficient": [],
            }
            _RECIPE_DETAIL_CACHE[recipe_id] = payload
            return jsonify(payload)

    return jsonify({"error": "Recipe not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
