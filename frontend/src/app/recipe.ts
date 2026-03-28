export interface Recipe {
  id: string;
  title: string;
  description: string;
  image: string;
  prepTime: string;
  cookTime: string;
  servings: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  tags?: string[];
  ingredients: Ingredient[];
  instructions: string[];
}

export interface Ingredient {
  id: string;
  name: string;
  amount: string;
  unit: string;
}