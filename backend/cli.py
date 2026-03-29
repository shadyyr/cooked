import sys

from quantities import (
    UNIT_MAP,
    parse_quantity,
    format_amount_unit,
    format_quantity_display,
    list_valid_units_text,
    suggest_unit_correction,
    validate_quantity_input,
    convert_amount_between_units,
    combine_quantities,
    parse_amount_unit,
)
from ingredients import (
    normalize_ingredient,
    assess_ingredient_confidence,
    resolve_ingredient_input_with_guidance,
    record_ingredient_observation,
)

def get_ingredients(fallback_recipes):
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
            normalized, confidence = resolve_ingredient_input_with_guidance(
                ingredient, fallback_recipes, prompt_label="Ingredient"
            )
            if normalized == "done":
                break
            if confidence == "suspicious":
                print(f"Accepted uncommon ingredient: {normalized}")
        else:
            assessment = assess_ingredient_confidence(ingredient, fallback_recipes)
            if assessment["status"] == "invalid":
                print(f"Skipping invalid ingredient '{ingredient}': {assessment['reason']}")
                continue
            normalized = assessment["normalized"]
            if assessment["status"] == "suspicious":
                hint = f" Suggestion: {assessment['suggestion']}." if assessment["suggestion"] else ""
                score = assessment.get("confidence_score")
                score_text = f" (confidence {score:.2f})" if score is not None else ""
                print(f"Uncommon ingredient '{ingredient}' accepted as '{normalized}'{score_text}.{hint}")

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
        record_ingredient_observation(normalized)

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


def add_more_ingredients(existing_ingredients, fallback_recipes):
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
            fallback_recipes,
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
        record_ingredient_observation(normalized)

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


def edit_ingredients(existing_ingredients, fallback_recipes):
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
                fallback_recipes,
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
            record_ingredient_observation(normalized_new)

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
