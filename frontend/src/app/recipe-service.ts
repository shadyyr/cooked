import { Recipe } from './recipe';

/**
 * Recipe Service - Handles data fetching from backend API
 * 
 * This service fetches recipes from the Python backend which uses:
 * - TheMealDB API for real recipe data
 * - Backend fallback recipes from `fallbacks.py` when API is unavailable
 * - Ingredient normalization and validation
 * 
 * The backend processes:
 * 1. User ingredients through validation layers
 * 2. Searches TheMealDB for matching recipes
 * 3. Extracts and normalizes ingredients and instructions
 * 4. Returns formatted recipe data for the frontend
 * 
 * Fallback behavior:
 * - Backend provides fallback recipe data when available
 * - If backend is unreachable, returns an empty list
 */

interface FetchRecipesOptions {
  search?: string;
}

interface IngredientValidationResult {
  valid: boolean;
  normalized?: string;
  reason?: string;
  suggestion?: string;
}

interface BackendRecipe {
  id?: string;
  recipe_name: string;
  description?: string;
  ingredients: {
    [key: string]: string;
  };
  instructions?: string[] | string;
  image_url?: string;
  youtube_url?: string;
  missing_details?: Array<{ ingredient: string; needed: string }>;
  missing?: string[];
  insufficient?: Array<{ ingredient: string; needed: string; have: string }>;
  match_percent?: number;
  score?: number;
  source?: string;
}

const RECIPE_META_KEYS = new Set([
  'image_url',
  'youtube_url',
  'description',
  'instructions',
]);

const DEFAULT_API_CANDIDATES = [
  'http://localhost:8000',
  'http://127.0.0.1:8000',
  'http://localhost:5000',
  'http://127.0.0.1:5000',
];

let workingApiBaseUrl: string | null = null;

function getApiBaseCandidates(): string[] {
  const configured = (process.env.NEXT_PUBLIC_API_URL || '').trim().replace(/\/+$/, '');
  if (configured) {
    return [configured, ...DEFAULT_API_CANDIDATES.filter((x) => x !== configured)];
  }
  return DEFAULT_API_CANDIDATES;
}

async function fetchBackend(path: string, init?: RequestInit): Promise<Response> {
  const candidates = getApiBaseCandidates();
  const ordered = workingApiBaseUrl
    ? [workingApiBaseUrl, ...candidates.filter((x) => x !== workingApiBaseUrl)]
    : candidates;

  const networkErrors: string[] = [];
  let lastBadResponse: Response | null = null;

  for (const baseUrl of ordered) {
    try {
      const response = await fetch(`${baseUrl}${path}`, init);
      if (response.ok) {
        workingApiBaseUrl = baseUrl;
        return response;
      }
      lastBadResponse = response;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      networkErrors.push(`${baseUrl}${path} -> ${message}`);
    }
  }

  if (lastBadResponse) {
    return lastBadResponse;
  }

  // Return a normal Response so callers can handle !ok without throwing TypeError.
  return new Response(
    JSON.stringify({
      error: "Backend unreachable",
      tried: ordered.map((baseUrl) => `${baseUrl}${path}`),
      details: networkErrors,
    }),
    {
      status: 503,
      headers: { "Content-Type": "application/json" },
    }
  );
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
  const ingredientEntries = Object.entries(backendRecipe.ingredients).filter(
    ([name]) => !RECIPE_META_KEYS.has(name)
  );
  const ingredients = ingredientEntries.map(([name, quantity], ingIndex) => ({
      id: `${index}-ing-${ingIndex}`,
      name: capitalizeWords(name),
      amount: extractAmount(quantity),
      unit: extractUnit(quantity),
    }));

  // Handle instructions - can be array or string with newlines
  let instructions: string[] = [];
  if (Array.isArray(backendRecipe.instructions)) {
    instructions = backendRecipe.instructions
      .map((step) => step.trim())
      .filter((step) => step.length > 0);
  } else if (typeof backendRecipe.instructions === 'string') {
    instructions = backendRecipe.instructions
      .split('\n')
      .map((step) => step.trim())
      .filter((step) => step.length > 0);
  }

  // Remove empty step headers like "Step 1" and strip prefixes like "STEP 2 - "
  instructions = instructions
    .map((step) => step.replace(/^step\s*\d+\s*[:.\-]?\s*/i, '').trim())
    .filter((step) => step.length > 0);

  // Ensure we have at least some instructions
  if (instructions.length === 0) {
    instructions = [
      'Prepare all ingredients and equipment.',
      'Follow the recipe method step by step.',
      'Adjust seasoning to taste and serve.',
    ];
  }

  // Generate recipe ID
  const recipeId = (backendRecipe.id || backendRecipe.recipe_name)
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '');

  const matchPercent =
    typeof backendRecipe.match_percent === 'number'
      ? backendRecipe.match_percent
      : Math.round((backendRecipe.score || 0) * 1000) / 10;
  const insufficientIngredients =
    (backendRecipe.insufficient || []).map((item) => item.ingredient) || [];
  const missingFromDetails =
    (backendRecipe.missing_details || []).map((item) => item.ingredient) || [];
  const missingIngredients = Array.from(
    new Set([...(backendRecipe.missing || []), ...missingFromDetails, ...insufficientIngredients])
  );

  return {
    id: recipeId,
    title: capitalizeWords(backendRecipe.recipe_name),
    description:
      backendRecipe.description ||
      `A delicious ${backendRecipe.recipe_name.toLowerCase()} recipe with ${ingredients.length} ingredients.`,
    image:
      backendRecipe.image_url ||
      getPlaceholderImage(index),
    matchPercent,
    missingIngredients,
    missingDetails: backendRecipe.missing_details || [],
    insufficientDetails: backendRecipe.insufficient || [],
    youtubeUrl: backendRecipe.youtube_url || undefined,
    source: backendRecipe.source || 'backend',
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
 * If no recipes are found from the backend, returns an empty list
 * 
 * Backend integration:
 * - Sends list of ingredients to Python backend
 * - Backend validates ingredients through 3-layer validation
 * - Searches TheMealDB API for matching recipes
 * - Extracts and normalizes ingredients
 * - Returns formatted recipe data
 * 
 * Fallback behavior:
 * - Backend handles fallback data from `fallbacks.py`
 * - If backend is unreachable, returns an empty list
 * - Logs which source is being used
 */
export async function getRecipes(
  options?: FetchRecipesOptions
): Promise<Recipe[]> {
  try {
    // Simulate API delay for development (optional)
    await new Promise((resolve) => setTimeout(resolve, 300));

    // For initial page load without ingredients, fetch backend fallback catalog
    if (!options?.search) {
      const response = await fetchBackend('/api/recipes/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ingredients: [],
          limit: 50,
          min_match_score: 0,
        }),
      });

      if (!response.ok) {
        console.log('Backend unavailable on initial load. Returning empty recipe list.');
        return [];
      }

      const data = await response.json();
      const backendRecipes: BackendRecipe[] = data.recipes || [];
      if (backendRecipes.length === 0) {
        console.log('Backend returned no initial recipes.');
        return [];
      }

      return backendRecipes.map((recipe, index) =>
        convertBackendRecipeToFrontend(recipe, index)
      );
    }

    const response = await fetchBackend('/api/recipes/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ingredients: [options.search],
        limit: 12,
        min_match_score: 0,
      }),
    });

    if (!response.ok) {
      console.warn(
        `Backend API request failed with status ${response.status}.`
      );
      return [];
    }

    const data = await response.json();
    const backendRecipes: BackendRecipe[] = data.recipes || [];

    // If no recipes found from backend, return empty list
    if (backendRecipes.length === 0) {
      console.log(`No recipes found from backend API for "${options.search}".`);
      return [];
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
      'Failed to fetch recipes from backend API:',
      error
    );
    return [];
  }
}

/**
 * Fetches recipes based on added ingredients from the ingredient modal
 * This is the main method called when user adds ingredients
 * If no recipes found from backend, returns an empty list
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
      console.log('No ingredients provided. Loading backend default recipes.');
      return getRecipes();
    }

    // Simulate API delay for development (optional)
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Send full ingredient payload (name + quantity + unit) to backend
    const ingredientPayload = ingredients.map((ing) => ({
      ingredient: ing.ingredient,
      quantity: ing.quantity,
      unit: ing.unit,
    }));

    const response = await fetchBackend('/api/recipes/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ingredients: ingredientPayload,
        limit: 12,
        min_match_score: 0,
      }),
    });

    if (!response.ok) {
      console.warn(
        `Backend API request failed with status ${response.status}.`
      );
      return [];
    }

    const data = await response.json();
    const backendRecipes: BackendRecipe[] = data.recipes || [];

    // If no recipes found from backend, return empty list
    if (backendRecipes.length === 0) {
      console.log(
        `No recipes found from backend API for ingredients: ${ingredientPayload
          .map((x) => x.ingredient)
          .join(', ')}.`
      );
      return [];
    }

    // Convert backend format to frontend Recipe format
    const recipes: Recipe[] = backendRecipes.map((recipe, index) =>
      convertBackendRecipeToFrontend(recipe, index)
    );

    const source = data.source || 'backend';
    if (data.debug) {
      console.log('Backend debug:', data.debug);
    }
    console.log(
      `Fetched ${recipes.length} recipes for ingredients: ${ingredientPayload
        .map((x) => x.ingredient)
        .join(', ')} from ${source}`
    );
    return recipes;
  } catch (error) {
    console.error(
      'Failed to fetch recipes by ingredients:',
      error
    );
    return [];
  }
}

/**
 * Fetches a single recipe by ID from the backend API
 * Returns null if not found in backend
 * 
 * Backend endpoint:
 * GET /api/recipes/{id}
 */
export async function getRecipeById(id: string): Promise<Recipe | null> {
  try {
    // Simulate API delay for development (optional)
    await new Promise((resolve) => setTimeout(resolve, 200));

    const response = await fetchBackend(`/api/recipes/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn(`Recipe ${id} not found (status ${response.status})`);
      return null;
    }

    const backendRecipe: BackendRecipe = await response.json();
    return convertBackendRecipeToFrontend(backendRecipe, 0);
  } catch (error) {
    console.error(`Failed to fetch recipe ${id}:`, error);
    return null;
  }
}

export async function validateIngredientName(
  ingredient: string
): Promise<IngredientValidationResult> {
  const response = await fetchBackend('/api/ingredients/validate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ingredient }),
  });

  const payload = await response.json().catch(() => ({}));
  if (response.ok) {
    return {
      valid: true,
      normalized: payload.normalized,
    };
  }
  return {
    valid: false,
    reason: payload.reason || 'Input is not recognized as a valid ingredient.',
    suggestion: payload.suggestion,
  };
}

export async function validateIngredientEntry(
  ingredient: string,
  unit: string
): Promise<IngredientValidationResult> {
  const response = await fetchBackend('/api/ingredients/validate-entry', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ingredient, unit }),
  });

  const payload = await response.json().catch(() => ({}));
  if (response.ok) {
    return {
      valid: true,
      normalized: payload.normalized,
    };
  }
  return {
    valid: false,
    reason: payload.reason || 'Ingredient/unit combination is not valid.',
    suggestion: payload.suggestion,
  };
}

export async function suggestUnitsForIngredient(
  ingredient: string
): Promise<string[]> {
  const response = await fetchBackend('/api/ingredients/suggest-units', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ingredient }),
  });

  if (!response.ok) {
    return [];
  }

  const payload = await response.json().catch(() => ({}));
  const units = Array.isArray(payload.units) ? payload.units : [];
  return units.map((u) => String(u).trim().toLowerCase()).filter(Boolean);
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
      recipe.ingredients?.some((ing) =>
        ing.name.toLowerCase().includes(lowerQuery)
      );

    return matchesSearch;
  });
}

