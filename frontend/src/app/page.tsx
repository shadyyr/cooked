'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { Recipe } from './recipe';
import { 
  getRecipes, 
  searchRecipes, 
  filterByDifficulty 
} from './recipe-service';

export default function RecipesLanding() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(
    null
  );

  // Fetch recipes on component mount
  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        setIsLoading(true);
        const data = await getRecipes();
        setRecipes(data);
      } catch (error) {
        console.error('Failed to fetch recipes:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecipes();
  }, []);

  // Filter recipes based on search and difficulty
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white">
      {/* Navigation */}
      <nav className="fixed w-full top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Cooked!</h1>
          <div className="flex gap-6 items-center">
            <Link href="#recipes" className="hover:text-blue-400 transition">
              Recipes
            </Link>
            <button className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-700 transition">
              Share Recipe
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-bold mb-6">
            Discover What's Possible
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Explore delicious recipes, scale ingredients, and create culinary masterpieces
          </p>
        </div>
      </section>

      {/* Search & Filter Section */}
      <section id="recipes" className="py-12 px-4 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          {/* Search Bar */}
          <div className="mb-8">
            <div className="relative">
              <input
                type="text"
                placeholder="Search recipes, ingredients, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-6 py-3 rounded-lg bg-slate-700 text-white placeholder-gray-400 border border-slate-600 focus:border-blue-400 outline-none transition"
              />
              <span className="absolute right-4 top-3 text-gray-400">🔍</span>
            </div>
          </div>

          {/* Difficulty Filter */}
          <div className="flex flex-wrap gap-2 items-center mb-8">
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
              <button
                key={difficulty}
                onClick={() => setSelectedDifficulty(difficulty)}
                className={`px-4 py-2 rounded-lg transition ${
                  selectedDifficulty === difficulty
                    ? 'bg-blue-600'
                    : 'bg-slate-700 hover:bg-slate-600'
                }`}
              >
                {difficulty}
              </button>
            ))}
          </div>

          {/* Results Count */}
          {!isLoading && (
            <p className="text-sm text-gray-400 mb-6">
              Showing {filteredRecipes.length} of {recipes.length} recipes
            </p>
          )}
        </div>
      </section>

      {/* Recipe Grid */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          {isLoading ? (
            <div className="text-center py-16">
              <p className="text-xl text-gray-300">Loading recipes...</p>
            </div>
          ) : filteredRecipes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRecipes.map((recipe) => (
                <Link
                  key={recipe.id}
                  href={`/recipes/${recipe.id}`}
                  className="group"
                >
                  <div className="bg-slate-700/50 rounded-lg overflow-hidden border border-slate-600 hover:border-blue-400 transition-all hover:transform hover:scale-105">
                    {/* Recipe Image */}
                    <div className="relative h-48 overflow-hidden bg-slate-800">
                      <img
                        src={recipe.image}
                        alt={recipe.title}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      />
                      {/* Difficulty Badge */}
                      <div className="absolute top-3 right-3">
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
                      </div>
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
                          <span className="text-gray-400">⏱️</span>
                          <p className="text-xs text-gray-400 mt-1">
                            {recipe.prepTime}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-400">🔥</span>
                          <p className="text-xs text-gray-400 mt-1">
                            {recipe.cookTime}
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-400">🍽️</span>
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
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <p className="text-xl text-gray-400 mb-4">
                No recipes found matching your search
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedDifficulty(null);
                }}
                className="text-blue-400 hover:text-blue-300 transition"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Footer CTA */}
      <section className="py-16 px-4 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <h3 className="text-3xl font-bold mb-4">Have a Recipe to Share?</h3>
          <p className="text-lg mb-8 text-blue-100">
            Contribute your favorite recipes to our growing collection
          </p>
          <button className="bg-white text-blue-600 px-8 py-3 rounded-lg text-lg font-bold hover:bg-gray-100 transition">
            Submit a Recipe
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-700 py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-gray-400">
          <p>&copy; 2026 RecipeHub. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}