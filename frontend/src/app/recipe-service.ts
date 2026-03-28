import { Recipe } from './recipe';

/**
 * Recipe Service - Handles data fetching
 * 
 * This service abstracts away the data source (hardcoded or API)
 * Making it easy to switch to API calls later without changing components
 * 
 * To switch to API: Simply replace getRecipes() implementation
 * Current: Returns mock data from mockRecipes.ts
 * Future: Will fetch from external API
 */

// Import mock recipes - can be replaced with API call later
import { mockRecipes } from './mockRecipes';

interface FetchRecipesOptions {
  search?: string;
  difficulty?: string;
}

/**
 * Fetches recipes - currently returns mock data
 * 
 * FUTURE API IMPLEMENTATION:
 * Replace the return statement with:
 * 
 * const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/recipes`, {
 *   params: {
 *     search,
 *     difficulty
 *   }
 * });
 * return response.json();
 */
export async function getRecipes(
  options?: FetchRecipesOptions
): Promise<Recipe[]> {
  // TODO: Replace with API call
  // const { search, difficulty } = options || {};
  
  // Simulate API delay for development
  await new Promise((resolve) => setTimeout(resolve, 300));

  return mockRecipes;
}

/**
 * Fetches a single recipe by ID
 * 
 * FUTURE API IMPLEMENTATION:
 * const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/recipes/${id}`);
 * return response.json();
 */
export async function getRecipeById(id: string): Promise<Recipe | null> {
  // TODO: Replace with API call
  
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 200));

  return mockRecipes.find((recipe) => recipe.id === id) || null;
}

/**
 * Searches recipes (client-side filtering for now)
 * 
 * FUTURE API IMPLEMENTATION:
 * const response = await fetch(
 *   `${process.env.NEXT_PUBLIC_API_URL}/recipes/search?q=${query}`
 * );
 * return response.json();
 */
export function searchRecipes(
  recipes: Recipe[],
  query: string
): Recipe[] {
  // TODO: Move to server-side API search for better performance at scale
  
  const lowerQuery = query.toLowerCase();
  return recipes.filter((recipe) => {
    const matchesSearch =
      recipe.title.toLowerCase().includes(lowerQuery) ||
      recipe.description.toLowerCase().includes(lowerQuery) ||
      recipe.tags?.some((tag) =>
        tag.toLowerCase().includes(lowerQuery)
      );

    return matchesSearch;
  });
}

/**
 * Filters recipes by difficulty
 */
export function filterByDifficulty(
  recipes: Recipe[],
  difficulty: string | null
): Recipe[] {
  if (!difficulty) return recipes;
  return recipes.filter((recipe) => recipe.difficulty === difficulty);
}