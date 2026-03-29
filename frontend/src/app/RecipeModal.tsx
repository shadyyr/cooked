'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Recipe } from './recipe';

interface RecipeModalProps {
  recipe: Recipe | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function RecipeModal({ recipe, isOpen, onClose }: RecipeModalProps) {
  const [checkedIngredients, setCheckedIngredients] = useState<Set<string>>(new Set());
  const [scaleFactor, setScaleFactor] = useState(1);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : 'unset';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const toggleIngredient = (id: string) => {
    const next = new Set(checkedIngredients);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setCheckedIngredients(next);
  };

  const getScaledAmount = (amount: string, factor: number) => {
    const num = parseFloat(amount);
    if (Number.isNaN(num)) return amount;
    return (num * factor).toFixed(2).replace(/\.?0+$/, '');
  };

  const formatShortBy = (shortBy?: { amount: number; unit?: string }) => {
    if (!shortBy) return null;
    const amount =
      Number.isInteger(shortBy.amount) ? String(shortBy.amount) : String(shortBy.amount);
    return `${amount}${shortBy.unit ? ` ${shortBy.unit}` : ''}`;
  };

  const getMatchBadgeClass = (matchPercent: number) => {
    if (matchPercent >= 70) {
      return 'bg-emerald-500/90 text-emerald-50';
    }
    if (matchPercent >= 40) {
      return 'bg-amber-500/90 text-amber-50';
    }
    return 'bg-rose-500/90 text-rose-50';
  };

  if (!recipe) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
          >
            <div className="relative bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-slate-700">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={onClose}
                className="absolute top-4 right-4 z-50 bg-slate-700 hover:bg-slate-600 rounded-full p-2 shadow-lg transition"
                aria-label="Close modal"
              >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </motion.button>

              <div className="p-8">
                <div className="mb-8">
                  <div className="flex flex-wrap gap-3 mb-6 items-start">
                    <h1 className="text-4xl font-bold text-white">{recipe.title}</h1>
                    <span
                      className={`self-start px-4 py-2 rounded-full text-sm font-semibold ${getMatchBadgeClass(
                        recipe.matchPercent
                      )}`}
                    >
                      {Math.round(recipe.matchPercent)}% match
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

                  <p className="text-lg text-gray-300 leading-relaxed mb-4">{recipe.description}</p>

                  <div className="bg-slate-700/40 border border-slate-600 rounded-lg p-4">
                    <div className="text-sm text-gray-300 space-y-2">
                      <p className="font-semibold">Missing or insufficient ingredients:</p>
                      {recipe.missingDetails && recipe.missingDetails.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-amber-300">
                          {recipe.missingDetails.map((item, idx) => (
                            <li key={`${item.ingredient}-${idx}`}>
                              {item.ingredient}: need {item.needed}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                      {recipe.insufficientDetails && recipe.insufficientDetails.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-orange-300">
                          {recipe.insufficientDetails.map((item, idx) => (
                            <li key={`${item.ingredient}-${idx}`}>
                              {item.ingredient}: have {item.have}, need {item.needed}
                              {item.short_by ? ` (need ${formatShortBy(item.short_by)} more)` : ''}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                      {(!recipe.missingDetails || recipe.missingDetails.length === 0) &&
                      (!recipe.insufficientDetails || recipe.insufficientDetails.length === 0) ? (
                        <p className="text-emerald-300">No missing ingredients.</p>
                      ) : null}
                    </div>
                    {recipe.youtubeUrl && (
                      <a
                        href={recipe.youtubeUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-block mt-2 text-sm text-red-300 hover:text-red-200 underline"
                      >
                        Watch recipe on YouTube
                      </a>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <motion.section
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <h2 className="text-2xl font-bold text-white mb-4">Ingredients</h2>

                    <div className="mb-6 p-4 bg-slate-700/40 rounded-lg border border-slate-600">
                      <label className="text-sm font-semibold text-gray-200 block mb-2">Scale Recipe:</label>
                      <select
                        value={scaleFactor}
                        onChange={(e) => setScaleFactor(parseFloat(e.target.value))}
                        className="w-full px-3 py-2 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 bg-slate-800 text-white"
                      >
                        <option value={0.5}>0.5x</option>
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
                          className="flex items-center p-3 rounded-lg hover:bg-slate-700/50 cursor-pointer transition-colors"
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
                                ? 'text-gray-500 line-through opacity-50'
                                : 'text-gray-300'
                            }`}
                          >
                            <span className="font-semibold text-sm">
                              {getScaledAmount(ingredient.amount, scaleFactor)} {ingredient.unit}
                            </span>
                            <span className="text-base">{ingredient.name}</span>
                          </span>
                        </motion.label>
                      ))}
                    </div>
                  </motion.section>

                  <motion.section
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <h2 className="text-2xl font-bold text-white mb-4">Recipe</h2>
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
                              ? 'bg-orange-600/20 border-orange-600 border-slate-600'
                              : 'bg-slate-700/30 border-transparent hover:bg-slate-700/50 border-slate-600'
                          }`}
                        >
                          <span className="font-bold text-orange-500 mr-3">Step {index + 1}</span>
                          <span className="text-gray-300 text-sm">{instruction}</span>
                        </motion.div>
                      ))}
                    </div>
                  </motion.section>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
