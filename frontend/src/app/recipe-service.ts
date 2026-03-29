import { Recipe } from './recipe';

/**
 * Recipe Service - Handles data fetching from backend API
 * 
 * This service fetches recipes from the Python backend which uses:
 * - TheMealDB API for real recipe data
 * - Local fallback recipes when API is unavailable
 * - Ingredient normalization and validation
 * 
 * The backend processes:
 * 1. User ingredients through validation layers
 * 2. Searches TheMealDB for matching recipes
 * 3. Extracts and normalizes ingredients and instructions
 * 4. Returns formatted recipe data for the frontend
 * 
 * Fallback behavior:
 * - If no recipes found from API, returns fallback recipes
 * - If API is unreachable, returns fallback recipes
 */

import { mockRecipes } from './mockRecipes';

interface FetchRecipesOptions {
  search?: string;
  difficulty?: string;
}

interface BackendRecipe {
  recipe_name: string;
  ingredients: {
    [key: string]: string;
  };
  instructions?: string[];
  image_url?: string;
  prep_time?: string;
  cook_time?: string;
  servings?: string;
  difficulty?: string;
  tags?: string[];
  score?: number;
  source?: string;
}

/**
 * Converts a backend recipe response into the frontend Recipe format
 * Handles the transformation from Python backend format to TypeScript Recipe interface
 */
function convertBackendRecipeToFrontend(
  backendRecipe: BackendRecipe,
  index: number
): Recipe {
  // Convert ingredients object to Ingredient array
  const ingredients = Object.entries(backendRecipe.ingredients).map(
    ([name, quantity], ingIndex) => ({
      id: `${index}-ing-${ingIndex}`,
      name: capitalizeWords(name),
      amount: extractAmount(quantity),
      unit: extractUnit(quantity),
    })
  );

  // Handle instructions - can be array or string with newlines
  let instructions: string[] = [];
  /*if (Array.isArray(backendRecipe.instructions)) {
    instructions = backendRecipe.instructions
      .map((step) => step.trim())
      .filter((step) => step.length > 0);
  } else if (typeof backendRecipe.instructions === 'string') {
    instructions = backendRecipe.instructions
      .split('\n')
      .map((step) => step.trim())
      .filter((step) => step.length > 0);
  }*/

  // Ensure we have at least some instructions
  if (instructions.length === 0) {
    instructions = [
      'Prepare all ingredients.',
      'Follow standard cooking procedures.',
      'Adjust seasonings to taste.',
      'Serve and enjoy!',
    ];
  }

  // Determine difficulty level
  let difficulty: 'Easy' | 'Medium' | 'Hard' = 'Easy';
  if (backendRecipe.difficulty) {
    const diff = backendRecipe.difficulty.toLowerCase();
    if (diff.includes('hard') || diff.includes('advanced') || diff === '3') {
      difficulty = 'Hard';
    } else if (diff.includes('medium') || diff.includes('intermediate') || diff === '2') {
      difficulty = 'Medium';
    }
  }

  // Generate recipe ID
  const recipeId = backendRecipe.recipe_name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '');

  return {
    id: recipeId,
    title: capitalizeWords(backendRecipe.recipe_name),
    description: `A delicious ${backendRecipe.recipe_name.toLowerCase()} recipe with ${ingredients.length} ingredients.`,
    image:
      backendRecipe.image_url ||
      getPlaceholderImage(index),
    prepTime: backendRecipe.prep_time || 'Unknown',
    cookTime: backendRecipe.cook_time || 'Unknown',
    servings: backendRecipe.servings || '4 servings',
    difficulty,
    tags: backendRecipe.tags || [],
    ingredients,
    instructions,
  };
}

/**
 * Capitalizes first letter of each word
 */
function capitalizeWords(text: string): string {
  return text
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Returns a different placeholder image based on index
 */
function getPlaceholderImage(index: number): string {
  const placeholders = [
    'https://images.unsplash.com/photo-1495635430265-7a9f718917be?w=800',
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800',
    'https://images.unsplash.com/photo-1504674900967-da07149fac95?w=800',
    'https://images.unsplash.com/photo-1567521464027-f127ff144326?w=800',
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800',
    'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800',
  ];
  return placeholders[index % placeholders.length];
}

/**
 * Extracts the amount from a quantity string
 * Examples: "2 cups" -> "2", "0.5 tbsp" -> "0.5", "1" -> "1"
 */
function extractAmount(quantity: string): string {
  if (!quantity) return '1';
  
  const match = quantity.match(/^[\d.]+/);
  if (match) {
    return match[0];
  }
  
  // Try to extract number from "1/2" format
  const fractionMatch = quantity.match(/(\d+)\/(\d+)/);
  if (fractionMatch) {
    const numerator = parseFloat(fractionMatch[1]);
    const denominator = parseFloat(fractionMatch[2]);
    return (numerator / denominator).toFixed(2);
  }
  
  return '1';
}

/**
 * Extracts the unit from a quantity string
 * Examples: "2 cups" -> "cup", "250 ml" -> "ml", "1 clove" -> "clove"
 */
function extractUnit(quantity: string): string {
  if (!quantity) return '';
  
  const match = quantity.match(/\s+([a-zA-Z]+)$/);
  if (match) {
    const unit = match[1].toLowerCase();
    
    // Normalize common variations
    const unitMap: { [key: string]: string } = {
      'cups': 'cup',
      'tablespoons': 'tbsp',
      'teaspoons': 'tsp',
      'grams': 'g',
      'kilograms': 'kg',
      'ounces': 'oz',
      'pounds': 'lb',
      'milliliters': 'ml',
      'liters': 'l',
      'cloves': 'clove',
      'slices': 'slice',
      'sticks': 'stick',
      'pieces': 'piece',
      'cans': 'can',
    };
    
    return unitMap[unit] || unit;
  }
  
  return '';
}

/**
 * Fetches recipes from the backend API based on ingredients
 * If no recipes are found from the backend, returns fallback recipes
 * 
 * Backend integration:
 * - Sends list of ingredients to Python backend
 * - Backend validates ingredients through 3-layer validation
 * - Searches TheMealDB API for matching recipes
 * - Extracts and normalizes ingredients
 * - Returns formatted recipe data
 * 
 * Fallback behavior:
 * - If API returns empty results, uses mockRecipes
 * - If API is unreachable, uses mockRecipes
 * - Logs which source is being used
 */
export async function getRecipes(
  options?: FetchRecipesOptions
): Promise<Recipe[]> {
  try {
    // Simulate API delay for development (optional)
    await new Promise((resolve) => setTimeout(resolve, 300));

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // For initial page load without ingredients, return fallback recipes
    if (!options?.search) {
      console.log('No search query provided. Using fallback recipes.');
      return mockRecipes;
    }

    const response = await fetch(`${apiUrl}/api/recipes/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ingredients: [options.search],
        limit: 12,
      }),
    });

    if (!response.ok) {
      console.warn(
        `Backend API request failed with status ${response.status}. Using fallback recipes.`
      );
      return mockRecipes;
    }

    const data = await response.json();
    const backendRecipes: BackendRecipe[] = data.recipes || [];

    // If no recipes found from API, use fallback recipes
    if (backendRecipes.length === 0) {
      console.log(
        `No recipes found from backend API for "${options.search}". Using fallback recipes.`
      );
      return mockRecipes;
    }

    // Convert backend format to frontend Recipe format
    const recipes: Recipe[] = backendRecipes.map((recipe, index) =>
      convertBackendRecipeToFrontend(recipe, index)
    );

    const source = data.source || 'backend';
    console.log(
      `Fetched ${recipes.length} recipes from ${source} via backend API`
    );
    return recipes;
  } catch (error) {
    console.error(
      'Failed to fetch recipes from backend API. Using fallback recipes:',
      error
    );
    return mockRecipes;
  }
}

/**
 * Fetches recipes based on added ingredients from the ingredient modal
 * This is the main method called when user adds ingredients
 * If no recipes found from API, returns fallback recipes
 * 
 * Usage:
 * const addedIngredients = [
 *   { id: '1', ingredient: 'egg', quantity: '2', unit: 'count' },
 *   { id: '2', ingredient: 'milk', quantity: '1', unit: 'cup' },
 *   { id: '3', ingredient: 'butter', quantity: '1', unit: 'tbsp' }
 * ];
 * const recipes = await fetchRecipesByIngredients(addedIngredients);
 */
export async function fetchRecipesByIngredients(
  ingredients: Array<{
    id: string;
    ingredient: string;
    quantity: string;
    unit: string;
  }>
): Promise<Recipe[]> {
  try {
    if (ingredients.length === 0) {
      console.log('No ingredients provided. Using fallback recipes.');
      return mockRecipes;
    }

    // Simulate API delay for development (optional)
    await new Promise((resolve) => setTimeout(resolve, 300));

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Extract just the ingredient names for the backend
    const ingredientNames = ingredients.map((ing) => ing.ingredient);

    const response = await fetch(`${apiUrl}/api/recipes/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ingredients: ingredientNames,
        limit: 12,
      }),
    });

    if (!response.ok) {
      console.warn(
        `Backend API request failed with status ${response.status}. Using fallback recipes.`
      );
      return mockRecipes;
    }

    const data = await response.json();
    const backendRecipes: BackendRecipe[] = data.recipes || [];

    // If no recipes found from API, use fallback recipes
    if (backendRecipes.length === 0) {
      console.log(
        `No recipes found from backend API for ingredients: ${ingredientNames.join(', ')}. Using fallback recipes.`
      );
      return mockRecipes;
    }

    // Convert backend format to frontend Recipe format
    const recipes: Recipe[] = backendRecipes.map((recipe, index) =>
      convertBackendRecipeToFrontend(recipe, index)
    );

    const source = data.source || 'backend';
    console.log(
      `Fetched ${recipes.length} recipes for ingredients: ${ingredientNames.join(', ')} from ${source}`
    );
    return recipes;
  } catch (error) {
    console.error(
      'Failed to fetch recipes by ingredients. Using fallback recipes:',
      error
    );
    return mockRecipes;
  }
}

/**
 * Fetches a single recipe by ID from the backend API
 * Falls back to searching mockRecipes if not found in API
 * 
 * Backend endpoint:
 * GET /api/recipes/{id}
 */
export async function getRecipeById(id: string): Promise<Recipe | null> {
  try {
    // Simulate API delay for development (optional)
    await new Promise((resolve) => setTimeout(resolve, 200));

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const response = await fetch(`${apiUrl}/api/recipes/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Try fallback recipes
      const fallbackRecipe = mockRecipes.find((recipe) => recipe.id === id);
      if (fallbackRecipe) {
        console.log(`Recipe ${id} not found in API. Using fallback recipe.`);
        return fallbackRecipe;
      }
      
      console.warn(`Recipe ${id} not found (status ${response.status})`);
      return null;
    }

    const backendRecipe: BackendRecipe = await response.json();
    return convertBackendRecipeToFrontend(backendRecipe, 0);
  } catch (error) {
    // Try fallback recipes on error
    const fallbackRecipe = mockRecipes.find((recipe) => recipe.id === id);
    if (fallbackRecipe) {
      console.log(
        `Failed to fetch recipe ${id} from API. Using fallback recipe:`,
        error
      );
      return fallbackRecipe;
    }
    
    console.error(`Failed to fetch recipe ${id}:`, error);
    return null;
  }
}

/**
 * Searches recipes by query string (client-side filtering)
 * Can be moved to backend for better performance at scale
 */
export function searchRecipes(
  recipes: Recipe[],
  query: string
): Recipe[] {
  const lowerQuery = query.toLowerCase();
  return recipes.filter((recipe) => {
    const matchesSearch =
      recipe.title.toLowerCase().includes(lowerQuery) ||
      recipe.description.toLowerCase().includes(lowerQuery) ||
      recipe.tags?.some((tag) => tag.toLowerCase().includes(lowerQuery)) ||
      recipe.ingredients?.some((ing) =>
        ing.name.toLowerCase().includes(lowerQuery)
      );

    return matchesSearch;
  });
}

/**
 * Filters recipes by difficulty level
 */
export function filterByDifficulty(
  recipes: Recipe[],
  difficulty: string | null
): Recipe[] {
  if (!difficulty) return recipes;
  return recipes.filter((recipe) => recipe.difficulty === difficulty);
}