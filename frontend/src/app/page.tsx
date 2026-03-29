'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Recipe } from './recipe';
import { 
  getRecipes, 
  searchRecipes, 
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
  
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoadingRecipe, setIsLoadingRecipe] = useState(false);

  // Ingredient modal state
  const [isIngredientModalOpen, setIsIngredientModalOpen] = useState(false);
  const [addedIngredients, setAddedIngredients] = useState<AddedIngredient[]>([]);
  const [isLoadingRecipes, setIsLoadingRecipes] = useState(false);
  const [editingIngredient, setEditingIngredient] = useState<AddedIngredient | null>(null);

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
    setEditingIngredient(null);
  };

  // When a new ingredient is added, fetch updated recipes
  const handleAddIngredient = async (ingredient: AddedIngredient) => {
    // Upsert ingredient in list (supports edit flow)
    const existingIndex = addedIngredients.findIndex((ing) => ing.id === ingredient.id);
    const updatedIngredients =
      existingIndex >= 0
        ? addedIngredients.map((ing) => (ing.id === ingredient.id ? ingredient : ing))
        : [...addedIngredients, ingredient];
    setAddedIngredients(updatedIngredients);

    // Fetch recipes based on all added ingredients
    const actionLabel = existingIndex >= 0 ? 'updated' : 'added';
    console.log(`Ingredient ${actionLabel}: ${ingredient.ingredient}. Fetching updated recipes...`);
    await fetchUpdatedRecipes(updatedIngredients);
  };

  const handleEditIngredient = (ingredient: AddedIngredient) => {
    setEditingIngredient(ingredient);
    setIsIngredientModalOpen(true);
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

    return results;
  }, [recipes, searchQuery]);

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
          <Link
            href="/"
            className="inline-flex items-center gap-3 rounded-xl px-2 py-1 hover:bg-slate-800/70 transition"
          >
            <span className="h-9 w-9 rounded-lg p-1.5 shadow-lg shadow-black/20 ring-1 ring-white/15">
              <img
                src="/favicon.ico"
                alt="Cooked logo"
                className="h-full w-full object-contain"
              />
            </span>
            <span className="text-2xl font-bold tracking-tight">Cooked!</span>
          </Link>
          <div className="flex gap-6 items-center">
            <Link href="#recipes" className="hover:text-blue-400 transition">
              Recipes
            </Link>
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

      {/* Search Section */}
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
                placeholder="Search recipes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-6 py-3 rounded-lg bg-slate-700 text-white placeholder-gray-400 border border-slate-600 focus:border-blue-400 outline-none transition"
              />
              <span className="absolute right-4 top-3 text-gray-400">🔍</span>
            </div>
          </motion.div>

          {/* Add Ingredient Button */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="flex items-center mb-8"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setEditingIngredient(null);
                setIsIngredientModalOpen(true);
              }}
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
                    className="inline-flex items-center gap-2 bg-orange-600/20 border border-orange-600/50 text-orange-300 px-3 py-2 rounded-full text-sm font-medium hover:bg-orange-600/30 transition group cursor-pointer"
                    onClick={() => handleEditIngredient(ingredient)}
                    title="Click to edit ingredient"
                  >
                    <span>
                      {ingredient.quantity} {ingredient.unit} {ingredient.ingredient}
                    </span>
                    <motion.button
                      whileHover={{ scale: 1.2 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveIngredient(ingredient.id);
                      }}
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
                      {/* Match Badge */}
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="absolute top-3 right-3"
                      >
                        <span
                          className="px-3 py-1 rounded-full text-sm font-semibold bg-blue-600/85"
                        >
                          {Math.round(recipe.matchPercent)}% match
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

                      {recipe.missingIngredients.length > 0 ? (
                        <p className="text-xs text-amber-300 mt-2">
                          Missing: {recipe.missingIngredients.slice(0, 4).join(', ')}
                          {recipe.missingIngredients.length > 4 ? '...' : ''}
                        </p>
                      ) : (
                        <p className="text-xs text-emerald-300 mt-2">No missing ingredients</p>
                      )}

                      {recipe.youtubeUrl && (
                        <a
                          href={recipe.youtubeUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-block mt-3 text-sm text-red-300 hover:text-red-200 underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          Watch on YouTube
                        </a>
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
                }}
                className="text-blue-400 hover:text-blue-300 transition"
              >
                Clear filters
              </motion.button>
            </motion.div>
          )}
        </div>
      </section>

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
        editingIngredient={editingIngredient}
        onAddIngredient={handleAddIngredient}
      />
    </div>
  );
}
