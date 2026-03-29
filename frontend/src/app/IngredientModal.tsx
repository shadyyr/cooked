'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface IngredientValue {
  id: string;
  ingredient: string;
  quantity: string;
  unit: string;
}

interface IngredientModalProps {
  isOpen: boolean;
  onClose: () => void;
  editingIngredient?: IngredientValue | null;
  onAddIngredient: (ingredient: IngredientValue) => void;
}

interface IngredientFormData {
  ingredient: string;
  quantity: string;
  unit: string;
}

const UNITS = [
  { value: 'count', label: 'Count' },
  { value: 'cup', label: 'Cup' },
  { value: 'tbsp', label: 'Tablespoon (tbsp)' },
  { value: 'tsp', label: 'Teaspoon (tsp)' },
  { value: 'g', label: 'Grams (g)' },
  { value: 'kg', label: 'Kilograms (kg)' },
  { value: 'oz', label: 'Ounces (oz)' },
  { value: 'lb', label: 'Pounds (lb)' },
  { value: 'ml', label: 'Milliliters (ml)' },
  { value: 'l', label: 'Liters (l)' },
  { value: 'clove', label: 'Clove' },
  { value: 'slice', label: 'Slice' },
  { value: 'stick', label: 'Stick' },
  { value: 'piece', label: 'Piece' },
  { value: 'can', label: 'Can' },
];

const MAX_INGREDIENT_LENGTH = 30;

export default function IngredientModal({
  isOpen,
  onClose,
  editingIngredient,
  onAddIngredient,
}: IngredientModalProps) {
  const [formData, setFormData] = useState<IngredientFormData>({
    ingredient: '',
    quantity: '',
    unit: '',
  });
  const [successMessage, setSuccessMessage] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    if (editingIngredient) {
      setFormData({
        ingredient: editingIngredient.ingredient,
        quantity: editingIngredient.quantity,
        unit: editingIngredient.unit,
      });
      setSuccessMessage(false);
      return;
    }
    setFormData({ ingredient: '', quantity: '', unit: '' });
    setSuccessMessage(false);
  }, [isOpen, editingIngredient]);

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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === 'ingredient' && value.length > MAX_INGREDIENT_LENGTH) return;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const resetForm = () => {
    setFormData({ ingredient: '', quantity: '', unit: '' });
    setSuccessMessage(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSave = () => {
    if (!formData.ingredient.trim() || !formData.quantity.trim() || !formData.unit) {
      alert('Please fill in all fields');
      return;
    }

    onAddIngredient({
      id: editingIngredient?.id || `${Date.now()}-${Math.random()}`,
      ingredient: formData.ingredient,
      quantity: formData.quantity,
      unit: formData.unit,
    });

    setSuccessMessage(true);
    setTimeout(() => setSuccessMessage(false), 1200);

    if (editingIngredient) {
      handleClose();
      return;
    }
    setFormData({ ingredient: '', quantity: '', unit: '' });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={handleClose}
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
            <div className="relative bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg shadow-2xl w-full max-w-md border border-slate-700">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleClose}
                className="absolute top-4 right-4 z-50 bg-slate-700 hover:bg-slate-600 rounded-full p-2 shadow-lg transition"
                aria-label="Close modal"
              >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </motion.button>

              <div className="p-8">
                <h1 className="text-3xl font-bold text-white mb-8">
                  {editingIngredient ? 'Edit Ingredient' : 'Add Ingredient'}
                </h1>

                <AnimatePresence>
                  {successMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.3 }}
                      className="mb-6 p-3 bg-green-600/20 border border-green-600/50 rounded-lg text-green-300 text-sm font-medium"
                    >
                      {editingIngredient ? 'Ingredient updated successfully!' : 'Ingredient added successfully!'}
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="space-y-6">
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-sm font-semibold text-gray-200">Ingredient Name</label>
                      <span className="text-xs text-gray-400">
                        {formData.ingredient.length}/{MAX_INGREDIENT_LENGTH}
                      </span>
                    </div>
                    <input
                      type="text"
                      name="ingredient"
                      value={formData.ingredient}
                      onChange={handleInputChange}
                      placeholder="e.g., Flour, Butter, Eggs..."
                      maxLength={MAX_INGREDIENT_LENGTH}
                      className="w-full px-4 py-2 bg-slate-700 text-white border border-slate-600 rounded-lg focus:border-orange-500 focus:outline-none transition"
                    />
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="grid grid-cols-3 gap-4"
                  >
                    <div className="col-span-1">
                      <label className="block text-sm font-semibold text-gray-200 mb-2">Quantity</label>
                      <input
                        type="number"
                        name="quantity"
                        value={formData.quantity}
                        onChange={handleInputChange}
                        placeholder="0.5"
                        step="0.01"
                        min="0"
                        className="w-full px-4 py-2 bg-slate-700 text-white border border-slate-600 rounded-lg focus:border-orange-500 focus:outline-none transition"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-semibold text-gray-200 mb-2">Unit</label>
                      <select
                        name="unit"
                        value={formData.unit}
                        onChange={handleInputChange}
                        className="w-full px-4 py-2 bg-slate-700 text-white border border-slate-600 rounded-lg focus:border-orange-500 focus:outline-none transition"
                      >
                        <option value="">Select a unit</option>
                        {UNITS.map((unit) => (
                          <option key={unit.value} value={unit.value}>
                            {unit.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="flex gap-4 pt-6"
                  >
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleClose}
                      className="flex-1 px-4 py-2 text-gray-300 border border-slate-600 rounded-lg hover:bg-slate-700/50 transition"
                    >
                      Close
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleSave}
                      className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition font-semibold"
                    >
                      {editingIngredient ? 'Save Changes' : 'Add Ingredient'}
                    </motion.button>
                  </motion.div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
