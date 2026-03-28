def get_ingredients():
    """
    Prompts the user to input ingredients they have in their pantry.
    Returns a list of ingredients entered by the user.
    """
    ingredients = []
    print("Enter the ingredients you have in your pantry.")
    print("Type 'done' when you are finished entering ingredients.")
    while True:
        ingredient = input("Ingredient: ").strip().lower()
        if ingredient == 'done':
            break
        if ingredient and ingredient not in ingredients:
            ingredients.append(ingredient)
            print(f"Added: {ingredient}")
        elif ingredient in ingredients:
            print(f"{ingredient} is already in your list.")
        else:
            print("Please enter a valid ingredient or 'done' to finish.")
    return ingredients

if __name__ == "__main__":
    user_ingredients = get_ingredients()
    print("\nYour ingredients:")
    for ing in user_ingredients:
        print(f"- {ing}")
    print(f"\nTotal ingredients: {len(user_ingredients)}")