# List of valid ingredients (singular forms, cooking/pantry items only)
VALID_INGREDIENTS = {
    "flour", "milk", "egg", "butter", "sugar", "salt", "pepper", "rice", "pasta", "bread", "cheese", "tomato", "onion", "garlic", "potato", "carrot",
    "lettuce", "spinach", "apple", "banana", "orange", "strawberry", "blueberry",
    "chicken broth", "olive oil", "vinegar", "soy sauce", "honey", "yeast", "baking powder",
    "baking soda", "cinnamon", "vanilla", "chocolate", "nut", "seed", "herb", "spice",
    "water", "oil", "cream", "yogurt", "sour cream", "mayonnaise", "ketchup", "mustard",
    "jam", "peanut butter", "jelly", "cereal", "oat", "cornflake", "bread crumb", "cracker",
    "frozen vegetable",
    "canned tomato", "canned bean", "lentil", "pea", "corn", "green bean", "broccoli",
    "cauliflower", "zucchini", "eggplant", "mushroom", "bell pepper", "jalapeno", "chili",
    "ginger", "turmeric", "cumin", "paprika", "oregano", "basil", "thyme", "rosemary", "sage",
    "parsley", "cilantro", "dill", "mint", "lemon", "lime", "orange juice", "apple juice",
    "milk chocolate", "dark chocolate", "white chocolate", "cocoa powder", "coffee", "tea",
    "syrup", "maple syrup", "agave",
    "brown sugar", "powdered sugar", "molasses", "cornstarch", "gelatin", "baking chocolate",
    "marshmallow", "sprinkle", "food coloring", "extract", "flavoring"
}

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
    Checks if an ingredient is valid by normalizing and checking against the list.
    """
    normalized = normalize_ingredient(ingredient)
    return normalized in VALID_INGREDIENTS

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
    "sticks": "stick"
}

def parse_amount_unit(quantity_input):
    """
    Parse quantity string into (amount, unit).
    Example: '2 eggs' -> (2.0, 'egg'), '1 cup milk' -> (1.0, 'cup'), '250ml' -> (250.0, 'ml').
    Returns (None, None) when parsing is not possible.
    """
    import re

    q = str(quantity_input).strip().lower()
    if not q:
        return None, None

    # number plus optional unit text; trailing words ignored
    pattern = r'^\s*(?P<num>\d+(?:\.\d+)?(?:/\d+)?)(?:\s+(?P<unit>[a-zA-Z]+))?.*$'
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
    """
    Returns True if pantry quantity satisfies required quantity.
    If parsing fails, falls back to existence-only check.
    """
    pantry_amt, pantry_unit = parse_amount_unit(pantry_quantity)
    required_amt, required_unit = parse_amount_unit(required_quantity)

    if required_amt is None:
        # Required quantity not parseable - assume presence is enough
        return pantry_quantity.strip() != ''

    if pantry_amt is None:
        # pantry quantity not parseable: assume they have enough (use presence)
        return True

    if required_unit and pantry_unit and required_unit != pantry_unit:
        # If units don't match, fall back to amount-only comparison for better UX
        return pantry_amt >= required_amt

    return pantry_amt >= required_amt


# Recipe database example (ingredient singular names and quantity requirement)
RECIPES = {
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
        'canned tomato': '1',
        'olive oil': '1 tbsp',
        'garlic': '1 clove'
    },
    'simple salad': {
        'lettuce': '1',
        'tomato': '1',
        'olive oil': '1 tbsp'
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
            insufficient.append({'ingredient': req_ing, 'needed': req_qty, 'have': pantry_qty})

    can_make = len(missing) == 0 and len(insufficient) == 0
    return can_make, missing, insufficient


def suggest_recipes(pantry):
    """
    Returns a list of suggested recipes based on pantry contents.
    Includes partial match scoring and sort by best candidate first.
    """
    suggestions = []

    for recipe_name, requirements in RECIPES.items():
        can_make, missing, insufficient = can_make_recipe(pantry, requirements)
        total = len(requirements)
        matched = total - len(missing)
        score = matched / total if total > 0 else 0.0
        suggestions.append({
            'recipe': recipe_name,
            'can_make': can_make,
            'missing': missing,
            'insufficient': insufficient,
            'score': score
        })

    # sort completed first, then high score, then fewest missing/insufficient
    suggestions.sort(key=lambda x: (not x['can_make'], -x['score'], len(x['missing']), len(x['insufficient'])))
    return suggestions



def get_ingredients():
    """
    Prompts the user to input ingredients they have in their pantry.
    Validates that inputs are actual ingredients.
    Returns a dict of ingredient name to quantity.
    """
    ingredients = {}
    print("Enter the ingredients you have in your pantry.")
    print("Type 'done' when you are finished entering ingredients.")
    while True:
        ingredient = input("Ingredient: ").strip().lower()
        if ingredient == 'done':
            break
        if not ingredient:
            print("Please enter a valid ingredient or 'done' to finish.")
            continue

        # Validate ingredient
        if not is_valid_ingredient(ingredient):
            print(f"'{ingredient}' is not recognized as a valid ingredient.")
            continue

        # Normalize name and handle duplicates in dict
        normalized = normalize_ingredient(ingredient)
        if normalized in ingredients:
            print(f"{normalized} is already in your list.")
            continue

        quantity_input = input("Quantity (e.g. 2 eggs, 1 cup, 250ml): ").strip()
        while not quantity_input:
            print("Please provide a quantity for this ingredient.")
            quantity_input = input("Quantity (e.g. 2 eggs, 1 cup, 250ml): ").strip()

        quantity = parse_quantity(quantity_input)

        ingredients[normalized] = quantity
        print(f"Added: {normalized} ({quantity})")

    return ingredients

if __name__ == "__main__":
    user_ingredients = get_ingredients()
    print("\nYour ingredients:")
    for ing, qty in user_ingredients.items():
        print(f"- {ing}: {qty}")
    print(f"\nTotal ingredients: {len(user_ingredients)}")

    suggestions = suggest_recipes(user_ingredients)
    print("\nRecipe suggestions:")
    for s in suggestions:
        status = "ready to make" if s['can_make'] else f"{s['score']*100:.0f}% matched"
        print(f"- {s['recipe']} ({status})")
        if s['missing']:
            print(f"  Missing: {', '.join(s['missing'])}")
        if s['insufficient']:
            for i in s['insufficient']:
                print(f"  Need more {i['ingredient']} ({i['needed']} vs {i['have']})")