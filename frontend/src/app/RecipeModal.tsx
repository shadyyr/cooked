'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Recipe, Ingredient } from './recipe';

interface RecipeModalProps {
  recipe: Recipe | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function RecipeModal({ recipe, isOpen, onClose }: RecipeModalProps) {
  const [checkedIngredients, setCheckedIngredients] = useState<Set<string>>(
    new Set()
  );
  const [scaleFactor, setScaleFactor] = useState(1);
  const [currentStep, setCurrentStep] = useState(0);

  // Close modal on Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const toggleIngredient = (id: string) => {
    const newChecked = new Set(checkedIngredients);
    if (newChecked.has(id)) {
      newChecked.delete(id);
    } else {
      newChecked.add(id);
    }
    setCheckedIngredients(newChecked);
  };

  const getScaledAmount = (amount: string, factor: number) => {
    const num = parseFloat(amount);
    return (num * factor).toFixed(2).replace(/\.?0+$/, '');
  };

  if (!recipe) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
          >
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
              {/* Close Button */}
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={onClose}
                className="fixed top-6 right-6 z-50 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition"
                aria-label="Close modal"
              >
                <svg
                  className="w-6 h-6 text-gray-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </motion.button>

              <div className="p-8">
                {/* Header */}
                <div className="mb-8">
                  <div className="flex gap-4 mb-6">
                    <h1 className="text-4xl font-bold text-gray-900">
                      {recipe.title}
                    </h1>
                    <span
                      className={`self-start px-4 py-2 rounded-full text-sm font-semibold ${
                        recipe.difficulty === 'Easy'
                          ? 'bg-green-100 text-green-800'
                          : recipe.difficulty === 'Medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {recipe.difficulty}
                    </span>
                  </div>

                  <motion.img
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    src={recipe.image}
                    alt={recipe.title}
                    className="w-full h-64 object-cover rounded-lg shadow-md mb-6"
                  />

                  <p className="text-lg text-gray-600 leading-relaxed mb-6">
                    {recipe.description}
                  </p>

                  {/* Recipe Meta */}
                  <div className="grid grid-cols-4 gap-4">
                    {[
                      { label: 'Prep Time', value: recipe.prepTime, icon: '⏱️' },
                      { label: 'Cook Time', value: recipe.cookTime, icon: '🔥' },
                      { label: 'Servings', value: recipe.servings, icon: '🍽️' },
                      { label: 'Difficulty', value: recipe.difficulty, icon: '⭐' },
                    ].map((item, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 + i * 0.05 }}
                        className="bg-gradient-to-br from-slate-50 to-slate-100 p-4 rounded-lg text-center border border-slate-200"
                      >
                        <span className="text-2xl block mb-2">{item.icon}</span>
                        <p className="text-xs uppercase font-semibold text-gray-500 mb-1">
                          {item.label}
                        </p>
                        <p className="text-lg font-bold text-gray-900">
                          {item.value}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Content Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Ingredients Section */}
                  <motion.section
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Ingredients
                    </h2>

                    {/* Scale Control */}
                    <div className="mb-6 p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <label className="text-sm font-semibold text-gray-700 block mb-2">
                        Scale Recipe:
                      </label>
                      <select
                        value={scaleFactor}
                        onChange={(e) => setScaleFactor(parseFloat(e.target.value))}
                        className="w-full px-3 py-2 border border-orange-200 rounded-lg focus:outline-none focus:border-orange-500"
                      >
                        <option value={0.5}>½x</option>
                        <option value={1}>1x</option>
                        <option value={1.5}>1.5x</option>
                        <option value={2}>2x</option>
                      </select>
                    </div>

                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {recipe.ingredients.map((ingredient, index) => (
                        <motion.label
                          key={ingredient.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.25 + index * 0.03 }}
                          className="flex items-center p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                        >
                          <input
                            type="checkbox"
                            checked={checkedIngredients.has(ingredient.id)}
                            onChange={() => toggleIngredient(ingredient.id)}
                            className="w-5 h-5 accent-orange-600 cursor-pointer flex-shrink-0"
                          />
                          <span
                            className={`ml-4 flex flex-col gap-0.5 ${
                              checkedIngredients.has(ingredient.id)
                                ? 'text-gray-400 line-through opacity-60'
                                : 'text-gray-700'
                            }`}
                          >
                            <span className="font-semibold text-sm">
                              {getScaledAmount(ingredient.amount, scaleFactor)}{' '}
                              {ingredient.unit}
                            </span>
                            <span className="text-base">{ingredient.name}</span>
                          </span>
                        </motion.label>
                      ))}
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setCheckedIngredients(new Set())}
                      className="mt-4 w-full px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                      Reset Checklist
                    </motion.button>
                  </motion.section>

                  {/* Instructions Section */}
                  <motion.section
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Instructions
                    </h2>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {recipe.instructions.map((instruction, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: 10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.25 + index * 0.03 }}
                          onClick={() => setCurrentStep(index)}
                          className={`p-4 rounded-lg cursor-pointer transition-all border-l-4 ${
                            currentStep === index
                              ? 'bg-orange-50 border-orange-600'
                              : 'bg-gray-50 border-transparent hover:bg-gray-100'
                          }`}
                        >
                          <span className="font-bold text-orange-600 mr-3">
                            Step {index + 1}
                          </span>
                          <span className="text-gray-700 text-sm">
                            {instruction}
                          </span>
                        </motion.div>
                      ))}
                    </div>
                  </motion.section>
                </div>

                {/* Tags */}
                {recipe.tags && recipe.tags.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="mt-8 pt-6 border-t border-gray-200"
                  >
                    <p className="text-sm font-semibold text-gray-700 mb-3">
                      Tags:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {recipe.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}