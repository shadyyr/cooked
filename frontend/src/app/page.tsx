'use client';

import { useState } from 'react';

interface Ingredient {
  id: string;
  name: string;
  amount: string;
  unit: string;
}

interface RecipePageProps {
  params: {
    id: string;
  };
}

export default function RecipePage({ params }: RecipePageProps) {
  const [checkedIngredients, setCheckedIngredients] = useState<Set<string>>(
    new Set()
  );

  // Mock recipe data
  const recipe = {
    id: params.id,
    title: 'Chocolate Chip Cookies',
    prepTime: '15 mins',
    cookTime: '12 mins',
    servings: '24 cookies',
    difficulty: 'Easy',
    image: 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=800',
    description:
      'Classic homemade chocolate chip cookies with a soft and chewy texture. Perfect for any occasion!',
    ingredients: [
      { id: '1', name: 'All-purpose flour', amount: '2', unit: 'cups' },
      { id: '2', name: 'Butter', amount: '1', unit: 'cup' },
      { id: '3', name: 'Granulated sugar', amount: '0.75', unit: 'cup' },
      { id: '4', name: 'Brown sugar', amount: '0.75', unit: 'cup' },
      { id: '5', name: 'Eggs', amount: '2', unit: 'large' },
      { id: '6', name: 'Vanilla extract', amount: '2', unit: 'tsp' },
      { id: '7', name: 'Baking soda', amount: '1', unit: 'tsp' },
      { id: '8', name: 'Salt', amount: '1', unit: 'tsp' },
      { id: '9', name: 'Chocolate chips', amount: '2', unit: 'cups' },
    ] as Ingredient[],
    instructions: [
      'Preheat oven to 375°F (190°C).',
      'In a large bowl, cream together butter and both sugars until light and fluffy.',
      'Beat in eggs one at a time, then stir in vanilla extract.',
      'In another bowl, combine flour, baking soda, and salt.',
      'Gradually blend the dry ingredients into the butter mixture.',
      'Stir in chocolate chips.',
      'Drop rounded tablespoons of dough onto ungreased cookie sheets.',
      'Bake for 9-12 minutes or until golden brown.',
      'Cool on baking sheets for 2 minutes, then transfer to wire racks.',
    ],
  };

  const toggleIngredient = (id: string) => {
    const newChecked = new Set(checkedIngredients);
    if (newChecked.has(id)) {
      newChecked.delete(id);
    } else {
      newChecked.add(id);
    }
    setCheckedIngredients(newChecked);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <header className="mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-6">{recipe.title}</h1>
        <img
          src={recipe.image}
          alt={recipe.title}
          className="w-full h-96 object-cover rounded-lg shadow-md mb-6"
        />
        <p className="text-lg text-gray-600 leading-relaxed mb-8">
          {recipe.description}
        </p>

        {/* Recipe Info Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-sm text-center">
            <span className="text-xs uppercase font-semibold text-gray-500 block mb-2">
              Prep Time
            </span>
            <span className="text-2xl font-bold text-orange-600">
              {recipe.prepTime}
            </span>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm text-center">
            <span className="text-xs uppercase font-semibold text-gray-500 block mb-2">
              Cook Time
            </span>
            <span className="text-2xl font-bold text-orange-600">
              {recipe.cookTime}
            </span>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm text-center">
            <span className="text-xs uppercase font-semibold text-gray-500 block mb-2">
              Servings
            </span>
            <span className="text-2xl font-bold text-orange-600">
              {recipe.servings}
            </span>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm text-center">
            <span className="text-xs uppercase font-semibold text-gray-500 block mb-2">
              Difficulty
            </span>
            <span className="text-2xl font-bold text-orange-600">
              {recipe.difficulty}
            </span>
          </div>
        </div>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Ingredients Section */}
        <section className="bg-white p-8 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Ingredients</h2>

          <div className="space-y-3">
            {recipe.ingredients.map((ingredient) => (
              <label
                key={ingredient.id}
                className="flex items-center p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={checkedIngredients.has(ingredient.id)}
                  onChange={() => toggleIngredient(ingredient.id)}
                  className="w-5 h-5 accent-orange-600 cursor-pointer flex-shrink-0"
                />
                <span
                  className={`ml-4 flex flex-col gap-1 ${
                    checkedIngredients.has(ingredient.id)
                      ? 'text-gray-400 line-through opacity-60'
                      : 'text-gray-700'
                  }`}
                >
                  <span className="font-semibold text-sm">
                    {ingredient.amount} {ingredient.unit}
                  </span>
                  <span className="text-base">{ingredient.name}</span>
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Instructions Section */}
        <section className="bg-white p-8 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Instructions</h2>
          <ol className="space-y-4 list-decimal list-inside">
            {recipe.instructions.map((instruction, index) => (
              <li
                key={index}
                className="text-gray-700 leading-relaxed marker:font-bold marker:text-orange-600"
              >
                {instruction}
              </li>
            ))}
          </ol>
        </section>
      </main>
    </div>
  );
}