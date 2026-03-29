'use client';

import { useState, useMemo, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Recipe } from './recipe';
import {
  getRecipes,
  searchRecipes,
  getRecipeById,
  fetchRecipesByIngredients,
} from './recipe-service';
import RecipeModal from './RecipeModal';
import IngredientModal from './IngredientModal';
import { auth, provider, db } from './firebase';
import {
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  User,
} from 'firebase/auth';
import {
  collection,
  doc,
  setDoc,
  deleteDoc,
  query,
  getDocs,
  onSnapshot,
  QueryDocumentSnapshot,
  QuerySnapshot,
  DocumentData,
} from 'firebase/firestore';

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

  // Auth + favorites
  const [user, setUser] = useState<User | null>(null);
  const [favoriteRecipeIds, setFavoriteRecipeIds] = useState<Set<string>>(new Set());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

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

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error('Google sign-in failed:', error);
    }
  };

  const signOutUser = async () => {
    try {
      await signOut(auth);
      setFavoriteRecipeIds(new Set());
      setShowFavoritesOnly(false);
    } catch (error) {
      console.error('Sign-out failed:', error);
    }
  };

  const loadFavorites = async (uid: string) => {
    try {
      const favQuery = query(collection(db, 'users', uid, 'favorites'));
      const snap = await getDocs(favQuery);
      const favIds = new Set<string>();
      snap.forEach((doc: QueryDocumentSnapshot<DocumentData>) => {
        favIds.add(doc.id);
      });
      setFavoriteRecipeIds(favIds);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser: User | null) => {
      if (firebaseUser) {
        setUser(firebaseUser);
        loadFavorites(firebaseUser.uid);

        // realtime sync favorites
        const favCollection = collection(db, 'users', firebaseUser.uid, 'favorites');
        const q = query(favCollection);
        const sub = onSnapshot(q, (snapshot: QuerySnapshot<DocumentData>) => {
          const liveFavs = new Set<string>();
          snapshot.forEach((docItem: QueryDocumentSnapshot<DocumentData>) => liveFavs.add(docItem.id));
          setFavoriteRecipeIds(liveFavs);
        });

        return () => sub();
      } else {
        setUser(null);
        setFavoriteRecipeIds(new Set());
      }
    });

    return () => unsubscribe();
  }, []);

  const toggleFavorite = async (recipe: Recipe) => {
    if (!user) {
      await signInWithGoogle();
      return;
    }

    const favDoc = doc(db, 'users', user.uid, 'favorites', recipe.id);
    if (favoriteRecipeIds.has(recipe.id)) {
      try {
        await deleteDoc(favDoc);
      } catch (error) {
        console.error('Failed to remove favorite:', error);
      }
    } else {
      try {
        await setDoc(favDoc, {
          recipeId: recipe.id,
          title: recipe.title,
          image: recipe.image,
          updatedAt: new Date(),
        });
      } catch (error) {
        console.error('Failed to add favorite:', error);
      }
    }
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

    if (showFavoritesOnly) {
      results = results.filter((recipe) => favoriteRecipeIds.has(recipe.id));
    }

    return results;
  }, [recipes, searchQuery, showFavoritesOnly, favoriteRecipeIds]);

  const CARD_EASE = [0.22, 1, 0.36, 1] as const;

  const getMatchBadgeClass = (matchPercent: number) => {
    if (matchPercent >= 70) {
      return 'bg-emerald-500/90 text-emerald-50';
    }
    if (matchPercent >= 40) {
      return 'bg-amber-500/90 text-amber-50';
    }
    return 'bg-rose-500/90 text-rose-50';
  };

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
      transition: { duration: 0.5, ease: CARD_EASE },
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
            onClick={() => {
              setSearchQuery('');
              setShowFavoritesOnly(false);
              setAddedIngredients([]);
            }}
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

          <div className="flex gap-4 items-center">
            <button
              onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
              className={`px-4 py-2 rounded-lg border font-semibold transition ${
                showFavoritesOnly
                  ? 'bg-blue-500/80 border-blue-400 text-white'
                  : 'bg-slate-700/70 border-slate-600 text-slate-100 hover:bg-slate-600/70'
              }`}
            >
              My Recipes
            </button>
            {user ? (
              <>
                <span className="text-sm text-slate-200 hidden md:inline-flex">{user.displayName}</span>
                <button
                  onClick={signOutUser}
                  className="px-4 py-2 text-sm rounded-lg bg-red-500/80 hover:bg-red-500 text-white"
                >
                  Sign out
                </button>
              </>
            ) : (
              <button
                onClick={signInWithGoogle}
                className="px-4 py-2 text-sm rounded-lg bg-green-600 hover:bg-green-500 text-white"
              >
                Sign in with Google
              </button>
            )}
          </div>
        </div>
      </motion.nav>

      {/* Top Search + Ingredient controls (screenshot style) */}
      <section className="pt-24 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 bg-slate-900/50 border border-slate-700/60 rounded-2xl p-4 shadow-2xl shadow-black/30 backdrop-blur-xl">
          <div className="w-full">
            <input
              type="text"
              placeholder="Search recipes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-14 px-5 rounded-xl bg-slate-800/80 border border-slate-700 text-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <button
            onClick={() => {
              setEditingIngredient(null);
              setIsIngredientModalOpen(true);
            }}
            className="w-full md:w-auto h-14 px-7 bg-orange-500 hover:bg-orange-400 text-white font-bold rounded-xl shadow-lg shadow-orange-500/25 transition flex items-center justify-center whitespace-nowrap"
          >
            + Add Ingredient
          </button>
        </div>

        {addedIngredients.length > 0 && (
          <div className="max-w-7xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: CARD_EASE }}
              className="mt-4 p-4 bg-slate-900/70 border border-slate-700 rounded-xl"
            >
              <p className="text-sm text-slate-300 mb-2 font-semibold">Selected Ingredients</p>
              <div className="flex flex-wrap gap-3">
                {addedIngredients.map((ingredient) => (
                  <motion.div
                    key={ingredient.id}
                    initial={{ opacity: 0, scale: 0.96, y: 4 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ duration: 0.2, ease: CARD_EASE }}
                    className="group inline-flex items-center rounded-full border border-slate-600 bg-slate-800/90 text-sm text-slate-100 shadow-sm shadow-black/25"
                  >
                    <button
                      onClick={() => handleEditIngredient(ingredient)}
                      className="px-3 py-2 font-medium hover:text-orange-200 transition"
                      title="Edit ingredient"
                    >
                      {ingredient.quantity} {ingredient.unit} {ingredient.ingredient}
                    </button>
                    <button
                      onClick={() => handleRemoveIngredient(ingredient.id)}
                      className="border-l border-slate-600 px-2 py-2 text-slate-400 transition hover:bg-slate-700 hover:text-slate-100 rounded-r-full"
                      aria-label="Remove ingredient"
                    >
                      x
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </section>

      {/* Search Section (simpler now) */}
      <section id="recipes" className="py-6 px-4">
        <div className="max-w-7xl mx-auto">

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
      <section className="py-10 px-4 bg-slate-900/20 border-t border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <div>
              <h2 className="text-3xl font-bold text-white">
                {showFavoritesOnly && user ? `Hey ${user.displayName?.split(' ')[0]}!` : 'Recipes for You'}
              </h2>
              <p className="text-slate-400 mt-1">
                {showFavoritesOnly && user
                  ? 'Your saved favorite recipes'
                  : addedIngredients.length > 0
                    ? 'Best matching recipes based on your ingredients'
                    : 'Discover delicious recipes to cook'}
              </p>
            </div>
          </div>
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
                    whileHover={{ scale: 1.02, translateY: -4 }}
                    transition={{ duration: 0.28, ease: CARD_EASE }}
                    className="bg-slate-900/40 backdrop-blur-xl rounded-2xl overflow-hidden border border-slate-600/70 hover:border-blue-300 hover:shadow-xl hover:shadow-blue-500/20 transition-all"
                  >
                    {/* Recipe Image */}
                    <div className="relative h-52 md:h-56 overflow-hidden bg-slate-900">
                      <motion.img
                        whileHover={{ scale: 1.05 }}
                        transition={{ duration: 0.35, ease: CARD_EASE }}
                        src={recipe.image}
                        alt={recipe.title}
                        className="w-full h-full object-cover"
                      />

                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 }}
                        className="absolute top-3 left-3 flex items-center gap-2"
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(recipe);
                          }}
                          className={`text-4xl leading-none transition ${
                            favoriteRecipeIds.has(recipe.id)
                              ? 'text-yellow-400 drop-shadow-lg'
                              : 'text-gray-300 hover:text-yellow-300'
                          }`}
                          aria-label={favoriteRecipeIds.has(recipe.id) ? 'Unfavorite' : 'Favorite'}
                        >
                          {favoriteRecipeIds.has(recipe.id) ? '★' : '☆'}
                        </button>
                      </motion.div>

                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2, ease: CARD_EASE }}
                        className="absolute top-3 right-3"
                      >
                        <span className={`px-3 py-1 rounded-full text-xs font-bold backdrop-blur-sm ${getMatchBadgeClass(recipe.matchPercent)}`}>
                          {Math.round(recipe.matchPercent)}% match
                        </span>
                      </motion.div>

                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/85 to-transparent p-3">
                        <div className="flex flex-wrap gap-2 text-[11px] font-semibold text-slate-100">
                          {recipe.prepTime && <span className="bg-black/40 rounded-full px-2 py-1">{recipe.prepTime}</span>}
                          {recipe.servings && <span className="bg-black/40 rounded-full px-2 py-1">{recipe.servings}</span>}
                          {recipe.difficulty && <span className="bg-black/40 rounded-full px-2 py-1">{recipe.difficulty}</span>}
                          {recipe.tags && recipe.tags.length > 0 && recipe.tags.slice(0, 2).map((tag) => (
                            <span key={tag} className="bg-black/40 rounded-full px-2 py-1">{tag}</span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Recipe Info */}
                    <div className="p-5 md:p-6 space-y-3">
                      <h3 className="text-xl md:text-2xl font-bold leading-tight text-slate-100 group-hover:text-orange-300 transition">
                        {recipe.title}
                      </h3>
                      <p className="text-slate-300 text-sm line-clamp-2">
                        {recipe.description}
                      </p>

                      <div>
                        <h4 className="text-xs text-zinc-300 uppercase tracking-widest font-semibold mb-1">Ingredient status</h4>
                        {recipe.missingIngredients.length > 0 ? (
                          <p className="text-xs text-amber-300">
                            Missing: {recipe.missingIngredients.slice(0, 3).join(', ')}
                            {recipe.missingIngredients.length > 3 ? '...' : ''}
                          </p>
                        ) : (
                          <p className="text-xs text-emerald-300">No missing ingredients</p>
                        )}
                      </div>

                      {recipe.youtubeUrl && (
                        <a
                          href={recipe.youtubeUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-block text-sm text-red-300 hover:text-red-200 underline"
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
              <p className="text-xl text-gray-400">
                No recipes found matching your search
              </p>
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

