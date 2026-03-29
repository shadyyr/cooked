export interface Recipe {
  id: string;
  title: string;
  description: string;
  image: string;
  matchPercent: number;
  missingIngredients: string[];
  missingDetails?: MissingIngredientDetail[];
  insufficientDetails?: InsufficientIngredientDetail[];
  youtubeUrl?: string;
  source?: string;
  ingredients: Ingredient[];
  instructions: string[];

  // Legacy optional fields retained temporarily for compatibility.
  prepTime?: string;
  cookTime?: string;
  servings?: string;
  difficulty?: 'Easy' | 'Medium' | 'Hard';
  tags?: string[];
}

export interface Ingredient {
  id: string;
  name: string;
  amount: string;
  unit: string;
}

export interface MissingIngredientDetail {
  ingredient: string;
  needed: string;
}

export interface InsufficientIngredientDetail {
  ingredient: string;
  needed: string;
  have: string;
  short_by?: {
    amount: number;
    unit?: string;
    unit_mismatch?: boolean;
  };
}
