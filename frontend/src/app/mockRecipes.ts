import { Recipe } from './recipe';

/**
 * Mock Recipes Data
 * 
 * This file serves as the temporary data source.
 * Replace this entire file or integrate with an API when ready.
 * 
 * Environment Variables to add for API integration:
 * NEXT_PUBLIC_API_URL=https://api.example.com
 * API_SECRET_KEY=your-secret-key
 */

export const mockRecipes: Recipe[] = [
  {
    id: 'chocolate-chip-cookies',
    title: 'Chocolate Chip Cookies',
    description:
      'Classic homemade chocolate chip cookies with a soft and chewy texture. Perfect for any occasion!',
    image:
      'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=800',
    matchPercent: 0,
    missingIngredients: [],
    prepTime: '15 mins',
    cookTime: '12 mins',
    servings: '24 cookies',
    difficulty: 'Easy',
    tags: ['dessert', 'baking', 'cookies', 'quick'],
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
    ],
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
  },
  {
    id: 'spaghetti-carbonara',
    title: 'Spaghetti Carbonara',
    description:
      'Authentic Italian pasta with creamy egg sauce, crispy guanciale, and Pecorino Romano cheese.',
    image:
      'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=800',
    matchPercent: 0,
    missingIngredients: [],
    prepTime: '10 mins',
    cookTime: '20 mins',
    servings: '4 servings',
    difficulty: 'Medium',
    tags: ['pasta', 'italian', 'dinner', 'quick'],
    ingredients: [
      { id: '1', name: 'Spaghetti', amount: '1', unit: 'lb' },
      { id: '2', name: 'Guanciale', amount: '6', unit: 'oz' },
      { id: '3', name: 'Eggs', amount: '4', unit: 'large' },
      { id: '4', name: 'Pecorino Romano', amount: '2', unit: 'cups' },
      { id: '5', name: 'Black pepper', amount: '1', unit: 'tsp' },
      { id: '6', name: 'Salt', amount: '1', unit: 'tsp' },
    ],
    instructions: [
      'Bring a large pot of salted water to boil.',
      'Cut guanciale into small cubes and cook until crispy.',
      'In a bowl, whisk together eggs, grated Pecorino, and black pepper.',
      'Cook spaghetti until al dente, then drain reserving 1 cup pasta water.',
      'Toss hot pasta with guanciale and fat.',
      'Remove from heat and quickly stir in egg mixture, adding pasta water as needed.',
      'Serve immediately with extra Pecorino and pepper.',
    ],
  },
  {
    id: 'beef-wellington',
    title: 'Beef Wellington',
    description:
      'Impressive beef tenderloin wrapped in mushroom duxelles and flaky puff pastry.',
    image:
      'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800',
    matchPercent: 0,
    missingIngredients: [],
    prepTime: '45 mins',
    cookTime: '45 mins',
    servings: '4-6 servings',
    difficulty: 'Hard',
    tags: ['beef', 'special-occasion', 'french', 'dinner'],
    ingredients: [
      { id: '1', name: 'Beef tenderloin', amount: '2', unit: 'lbs' },
      { id: '2', name: 'Mushrooms', amount: '1', unit: 'lb' },
      { id: '3', name: 'Puff pastry', amount: '1', unit: 'sheet' },
      { id: '4', name: 'Pâté', amount: '4', unit: 'oz' },
      { id: '5', name: 'Shallots', amount: '2', unit: 'medium' },
      { id: '6', name: 'Garlic', amount: '3', unit: 'cloves' },
    ],
    instructions: [
      'Sear beef on all sides until browned.',
      'Let cool and brush with mustard and pâté.',
      'Prepare mushroom duxelles with finely chopped mushrooms, shallots, and garlic.',
      'Wrap beef with duxelles mixture.',
      'Wrap in prosciutto, then puff pastry.',
      'Bake at 425°F for 25-30 minutes until golden.',
      'Rest for 10 minutes before serving.',
    ],
  },
  {
    id: 'greek-salad',
    title: 'Greek Salad',
    description:
      'Fresh Mediterranean salad with crisp vegetables, feta cheese, and Kalamata olives.',
    image:
      'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800',
    matchPercent: 0,
    missingIngredients: [],
    prepTime: '15 mins',
    cookTime: '0 mins',
    servings: '4 servings',
    difficulty: 'Easy',
    tags: ['salad', 'vegetarian', 'mediterranean', 'healthy', 'quick'],
    ingredients: [
      { id: '1', name: 'Tomatoes', amount: '4', unit: 'medium' },
      { id: '2', name: 'Cucumbers', amount: '2', unit: 'large' },
      { id: '3', name: 'Red onion', amount: '1', unit: 'medium' },
      { id: '4', name: 'Kalamata olives', amount: '1', unit: 'cup' },
      { id: '5', name: 'Feta cheese', amount: '8', unit: 'oz' },
      { id: '6', name: 'Olive oil', amount: '3', unit: 'tbsp' },
    ],
    instructions: [
      'Chop tomatoes and cucumbers into bite-sized pieces.',
      'Thinly slice red onion.',
      'Combine vegetables in a large bowl.',
      'Add olives and crumbled feta cheese.',
      'Drizzle with olive oil and toss gently.',
      'Serve immediately.',
    ],
  },
  {
    id: 'ramen',
    title: 'Homemade Ramen',
    description:
      'Silky noodles in a rich tonkotsu broth with soft-boiled eggs and tender chashu pork.',
    image:
      'https://images.unsplash.com/photo-1564621592915-38bea6a6a7f1?w=800',
    matchPercent: 0,
    missingIngredients: [],
    prepTime: '30 mins',
    cookTime: '180 mins',
    servings: '2 servings',
    difficulty: 'Hard',
    tags: ['noodles', 'japanese', 'soup', 'dinner'],
    ingredients: [
      { id: '1', name: 'Pork bones', amount: '3', unit: 'lbs' },
      { id: '2', name: 'Ramen noodles', amount: '2', unit: 'portions' },
      { id: '3', name: 'Eggs', amount: '2', unit: 'large' },
      { id: '4', name: 'Pork belly', amount: '1', unit: 'lb' },
      { id: '5', name: 'Green onions', amount: '2', unit: 'stalks' },
      { id: '6', name: 'Soy sauce', amount: '4', unit: 'tbsp' },
    ],
    instructions: [
      'Simmer pork bones for 3+ hours to create broth.',
      'Braise pork belly until tender.',
      'Soft boil eggs for 6-7 minutes.',
      'Cook ramen noodles in boiling water.',
      'Assemble bowl with noodles, broth, and toppings.',
      'Garnish with green onions and sesame seeds.',
    ],
  },
];
