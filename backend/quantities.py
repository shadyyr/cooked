import re
import difflib

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

def parse_quantity(quantity_input):
    """
    Accepts quantity input as text and returns sanitized quantity string.
    """
    return quantity_input.strip()

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

def suggest_unit_correction(unit_text):
    candidate_units = sorted(set(UNIT_MAP.values()))
    return find_best_text_match(unit_text, candidate_units)

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

    # default to "count" if no unit provided
    if not unit:
        unit = "count"

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

    # Same units or one/both missing units: normal numeric comparison
    if pantry_unit == required_unit:
        short_amt = max(0.0, required_amt - pantry_amt)
        if short_amt <= 0:
            return None
        return {
            "amount": round(short_amt, 3),
            "unit": required_unit or pantry_unit,
            "unit_mismatch": False,
        }

    # Try conversion when units differ
    if pantry_unit and required_unit and pantry_unit != required_unit:
        converted = convert_amount_between_units(pantry_amt, pantry_unit, required_unit)
        if converted is not None:
            short_amt = max(0.0, required_amt - converted)
            if short_amt <= 0:
                return None
            return {
                "amount": round(short_amt, 3),
                "unit": required_unit,
                "unit_mismatch": False,
            }

    # Units differ and could not be converted safely
    short_amt = max(0.0, required_amt - pantry_amt)
    if short_amt <= 0:
        return None

    return {
        "amount": round(short_amt, 3),
        "unit": required_unit or pantry_unit,
        "unit_mismatch": True,
    }