'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Recipe } from './recipe';
import { 
  getRecipes, 
  searchRecipes, 
  filterByDifficulty,
  getRecipeById,
  fetchRecipesByIngredients
} from './recipe-service';
import RecipeModal from './RecipeModal';
import IngredientModal from './IngredientModal';

interface AddedIngredient {
  id: string;
  ingredient: string;
  quantity: string;
  unit: string;
}

export default function RecipesLanding() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null);
  
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoadingRecipe, setIsLoadingRecipe] = useState(false);

  // Ingredient modal state
  const [isIngredientModalOpen, setIsIngredientModalOpen] = useState(false);
  const [addedIngredients, setAddedIngredients] = useState<AddedIngredient[]>([]);
  const [isLoadingRecipes, setIsLoadingRecipes] = useState(false);

  // Load initial recipes (fallback) on mount
  useEffect(() => {
    const loadInitialRecipes = async () => {
      try {
        setIsLoading(true);
        const data = await getRecipes();
        setRecipes(data);
      } catch (error) {
        console.error('Failed to fetch initial recipes:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialRecipes();
  }, []);

  const handleRecipeClick = async (recipe: Recipe) => {
    try {
      setIsLoadingRecipe(true);
      const fullRecipe = await getRecipeById(recipe.id);
      if (fullRecipe) {
        setSelectedRecipe(fullRecipe);
        setIsModalOpen(true);
      }
    } catch (error) {
      console.error('Failed to fetch recipe details:', error);
    } finally {
      setIsLoadingRecipe(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setTimeout(() => setSelectedRecipe(null), 300);
  };

  const handleCloseIngredientModal = () => {
    setIsIngredientModalOpen(false);
  };

  // When a new ingredient is added, fetch updated recipes
  const handleAddIngredient = async (ingredient: AddedIngredient) => {
    // Add ingredient to list
    const updatedIngredients = [...addedIngredients, ingredient];
    setAddedIngredients(updatedIngredients);

    // Fetch recipes based on all added ingredients
    console.log(`Ingredient added: ${ingredient.ingredient}. Fetching updated recipes...`);
    await fetchUpdatedRecipes(updatedIngredients);
  };

  // Fetch recipes based on current added ingredients
  const fetchUpdatedRecipes = async (ingredients: AddedIngredient[]) => {
    try {
      setIsLoadingRecipes(true);
      console.log(`Fetching recipes for ${ingredients.length} ingredients...`);
      
      const updatedRecipes = await fetchRecipesByIngredients(ingredients);
      setRecipes(updatedRecipes);
      
      console.log(`Updated recipe list with ${updatedRecipes.length} recipes`);
    } catch (error) {
      console.error('Failed to fetch updated recipes:', error);
    } finally {
      setIsLoadingRecipes(false);
    }
  };

  const handleRemoveIngredient = async (id: string) => {
    const updatedIngredients = addedIngredients.filter((ing) => ing.id !== id);
    setAddedIngredients(updatedIngredients);

    // Refetch recipes with updated ingredient list
    console.log(
      `Ingredient removed. Fetching updated recipes for ${updatedIngredients.length} ingredients...`
    );
    
    if (updatedIngredients.length === 0) {
      // If no ingredients left, load fallback recipes
      const data = await getRecipes();
      setRecipes(data);
    } else {
      await fetchUpdatedRecipes(updatedIngredients);
    }
  };

  const filteredRecipes = useMemo(() => {
    let results = recipes;

    if (searchQuery) {
      results = searchRecipes(results, searchQuery);
    }

    if (selectedDifficulty) {
      results = filterByDifficulty(results, selectedDifficulty);
    }

    return results;
  }, [recipes, searchQuery, selectedDifficulty]);

  const difficulties = Array.from(new Set(recipes.map((r) => r.difficulty)));

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      {/* Navigation */}
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
        className="fixed w-full top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-700"
      >
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Cooked !</h1>
          <div className="flex gap-6 items-center">
            <Link href="#recipes" className="hover:text-blue-400 transition">
              Recipes
            </Link>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Share Recipe
            </motion.button>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto text-center"
        >
          <h2 className="text-5xl md:text-6xl font-bold mb-6">
            Discover What's Possible
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Explore delicious recipes, scale ingredients, and create culinary masterpieces
          </p>
        </motion.div>
      </section>

      {/* Search & Filter Section */}
      <section id="recipes" className="py-12 px-4 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mb-8"
          >
            <div className="relative">
              <input
                type="text"
                placeholder="Search by recipes or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-6 py-3 rounded-lg bg-slate-700 text-white placeholder-gray-400 border border-slate-600 focus:border-blue-400 outline-none transition"
              />
              <span className="absolute right-4 top-3 text-gray-400">🔍</span>
            </div>
          </motion.div>

          {/* Difficulty Filter and Add Ingredient Button */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="flex flex-wrap gap-2 items-center mb-8"
          >
            <span className="text-sm font-semibold text-gray-300">
              Filter by difficulty:
            </span>
            <button
              onClick={() => setSelectedDifficulty(null)}
              className={`px-4 py-2 rounded-lg transition ${
                selectedDifficulty === null
                  ? 'bg-blue-600'
                  : 'bg-slate-700 hover:bg-slate-600'
              }`}
            >
              All
            </button>
            {difficulties.map((difficulty) => (
              <motion.button
                key={difficulty}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedDifficulty(difficulty)}
                className={`px-4 py-2 rounded-lg transition ${
                  selectedDifficulty === difficulty
                    ? 'bg-blue-600'
                    : 'bg-slate-700 hover:bg-slate-600'
                }`}
              >
                {difficulty}
              </motion.button>
            ))}

            {/* Add Ingredient Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsIngredientModalOpen(true)}
              className="ml-auto px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg transition font-semibold"
            >
              + Add Ingredient
            </motion.button>
          </motion.div>

          {/* Added Ingredients Display */}
          {addedIngredients.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-8 p-4 bg-orange-600/10 border border-orange-600/30 rounded-lg"
            >
              <p className="text-sm font-semibold text-gray-300 mb-3">
                Selected Ingredients:
              </p>
              <div className="flex flex-wrap gap-2">
                {addedIngredients.map((ingredient) => (
                  <motion.div
                    key={ingredient.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="inline-flex items-center gap-2 bg-orange-600/20 border border-orange-600/50 text-orange-300 px-3 py-2 rounded-full text-sm font-medium hover:bg-orange-600/30 transition group"
                  >
                    <span>
                      {ingredient.quantity} {ingredient.unit} {ingredient.ingredient}
                    </span>
                    <motion.button
                      whileHover={{ scale: 1.2 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleRemoveIngredient(ingredient.id)}
                      className="ml-1 text-orange-400 hover:text-orange-200 transition opacity-0 group-hover:opacity-100"
                      aria-label="Remove ingredient"
                    >
                      ✕
                    </motion.button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Results Count */}
          {!isLoading && !isLoadingRecipes && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm text-gray-400 mb-6"
            >
              Showing {filteredRecipes.length} of {recipes.length} recipes
              {addedIngredients.length > 0 && (
                <span> based on {addedIngredients.length} ingredient(s)</span>
              )}
            </motion.p>
          )}
        </div>
      </section>

      {/* Recipe Grid */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          {isLoading || isLoadingRecipes ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <p className="text-xl text-gray-300">
                {isLoading ? 'Loading recipes...' : 'Updating recipes...'}
              </p>
            </motion.div>
          ) : filteredRecipes.length > 0 ? (
            <motion.div
              key={filteredRecipes.length}
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {filteredRecipes.map((recipe) => (
                <motion.div
                  key={recipe.id}
                  variants={itemVariants}
                  onClick={() => handleRecipeClick(recipe)}
                  className="cursor-pointer"
                >
                  <motion.div
                    whileHover={{ scale: 1.05, translateY: -5 }}
                    transition={{ duration: 0.3 }}
                    className="bg-slate-700/50 rounded-lg overflow-hidden border border-slate-600 hover:border-blue-400 transition-all"
                  >
                    {/* Recipe Image */}
                    <div className="relative h-48 overflow-hidden bg-slate-800">
                      <motion.img
                        whileHover={{ scale: 1.1 }}
                        transition={{ duration: 0.3 }}
                        src={recipe.image}
                        alt={recipe.title}
                        className="w-full h-full object-cover"
                      />
                      {/* Difficulty Badge */}
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="absolute top-3 right-3"
                      >
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            recipe.difficulty === 'Easy'
                              ? 'bg-green-500/80'
                              : recipe.difficulty === 'Medium'
                              ? 'bg-yellow-500/80'
                              : 'bg-red-500/80'
                          }`}
                        >
                          {recipe.difficulty}
                        </span>
                      </motion.div>
                    </div>

                    {/* Recipe Info */}
                    <div className="p-6">
                      <h3 className="text-xl font-bold mb-2 group-hover:text-blue-400 transition">
                        {recipe.title}
                      </h3>
                      <p className="text-gray-300 text-sm mb-4 line-clamp-2">
                        {recipe.description}
                      </p>

                      {/* Recipe Meta */}
                      <div className="grid grid-cols-3 gap-3 mb-4 text-center text-sm">
                        <div>
                          <span className="text-gray-400">Prep Time: </span>
                          <p className="text-xs text-gray-400 mt-1">
                            {recipe.prepTime}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-400">Cook Time: </span>
                          <p className="text-xs text-gray-400 mt-1">
                            {recipe.cookTime}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-400">Servings: </span>
                          <p className="text-xs text-gray-400 mt-1">
                            {recipe.servings}
                          </p>
                        </div>
                      </div>

                      {/* Tags */}
                      {recipe.tags && recipe.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {recipe.tags.slice(0, 2).map((tag) => (
                            <span
                              key={tag}
                              className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded border border-blue-600/50"
                            >
                              {tag}
                            </span>
                          ))}
                          {recipe.tags.length > 2 && (
                            <span className="text-xs text-gray-400">
                              +{recipe.tags.length - 2} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <p className="text-xl text-gray-400 mb-4">
                No recipes found matching your search
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setSearchQuery('');
                  setSelectedDifficulty(null);
                }}
                className="text-blue-400 hover:text-blue-300 transition"
              >
                Clear filters
              </motion.button>
            </motion.div>
          )}
        </div>
      </section>

      {/* Footer CTA */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="py-16 px-4 bg-blue-600"
      >
        <div className="max-w-4xl mx-auto text-center">
          <h3 className="text-3xl font-bold mb-4">Have a Recipe to Share?</h3>
          <p className="text-lg mb-8 text-blue-100">
            Contribute your favorite recipes to our growing collection
          </p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-white text-blue-600 px-8 py-3 rounded-lg text-lg font-bold hover:bg-gray-100 transition"
          >
            Submit a Recipe
          </motion.button>
        </div>
      </motion.section>

      {/* Recipe Modal */}
      <RecipeModal
        recipe={selectedRecipe}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />

      {/* Ingredient Modal */}
      <IngredientModal
        isOpen={isIngredientModalOpen}
        onClose={handleCloseIngredientModal}
        onAddIngredient={handleAddIngredient}
      />
    </div>
  );
}