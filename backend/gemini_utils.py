import json
from config import GEMINI_API_KEY

try:
    import google.generativeai as genai
except ImportError:
    genai = None

if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def validate_ingredient_with_gemini(ingredient_text):
    """
    Uses Gemini to determine if a string is a legitimate cooking ingredient.
    """
    if not model:
        return None

    prompt = (
        f"Decide if '{ingredient_text}' is a legitimate cooking ingredient. "
        "Return a JSON object with 'is_valid' (boolean) and 'reason' (string). "
        "Ignore quantities or units, just focus on the item name itself."
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini Validation Error: {e}")
        return None

def convert_units_with_gemini(amount, from_unit, to_unit, ingredient_name):
    """
    Fallback for complex conversions (e.g., '3 cloves' to 'grams' or '1 onion' to 'cups').
    """
    if not model:
        return None

    prompt = (
        f"Convert {amount} {from_unit} of {ingredient_name} to {to_unit}. "
        "If the conversion depends on density or average size, provide your best estimate. "
        "Return a JSON object with 'converted_amount' (float) or null if impossible."
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        return data.get("converted_amount")
    except Exception as e:
        print(f"Gemini Conversion Error: {e}")
        return None


def validate_ingredient_unit_with_gemini(ingredient_name, unit):
    """
    Uses Gemini to validate whether a measurement unit is plausible for an ingredient.
    Example invalid: "slice of rice"
    """
    if not model:
        return None

    prompt = (
        f"Is '{unit}' a reasonable measurement unit for ingredient '{ingredient_name}' in cooking? "
        "Return JSON with keys: "
        "'is_valid' (boolean), "
        "'reason' (string), "
        "'suggested_units' (array of short unit strings, may be empty)."
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        if isinstance(data, dict):
            return data
        return None
    except Exception as e:
        print(f"Gemini Unit Validation Error: {e}")
        return None


def suggest_units_for_ingredient_with_gemini(ingredient_name, valid_units):
    """
    Ask Gemini for likely cooking units for an ingredient.
    """
    if not model:
        return None

    unit_list = ", ".join(valid_units)
    prompt = (
        f"From this allowed unit list: [{unit_list}], pick the units that make sense for "
        f"ingredient '{ingredient_name}' in cooking. "
        "Return strict JSON with key 'units' as an array of unit strings from the allowed list only."
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        if not isinstance(data, dict):
            return None
        raw_units = data.get("units") or []
        if not isinstance(raw_units, list):
            return None
        normalized = []
        valid_set = set(valid_units)
        for unit in raw_units:
            unit_text = str(unit).strip().lower()
            if unit_text in valid_set:
                normalized.append(unit_text)
        return list(dict.fromkeys(normalized))
    except Exception as e:
        print(f"Gemini Unit Suggestion Error: {e}")
        return None
