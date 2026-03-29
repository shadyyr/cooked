'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface IngredientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddIngredient: (ingredient: {
    id: string;
    ingredient: string;
    quantity: string;
    unit: string;
  }) => void;
}

interface IngredientFormData {
  ingredient: string;
  quantity: string;
  unit: string;
}

// Units mapping - standardized unit values
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
  onAddIngredient,
}: IngredientModalProps) {
  const [formData, setFormData] = useState<IngredientFormData>({
    ingredient: '',
    quantity: '',
    unit: '',
  });

  const [successMessage, setSuccessMessage] = useState(false);

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

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    // Limit ingredient name to 30 characters
    if (name === 'ingredient' && value.length > MAX_INGREDIENT_LENGTH) {
      return;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddIngredient = () => {
    if (!formData.ingredient.trim() || !formData.quantity.trim() || !formData.unit) {
      alert('Please fill in all fields');
      return;
    }

    // Generate unique ID
    const id = `${Date.now()}-${Math.random()}`;

    // Call parent callback with ingredient data
    onAddIngredient({
      id,
      ingredient: formData.ingredient,
      quantity: formData.quantity,
      unit: formData.unit,
    });

    // Show success message
    setSuccessMessage(true);
    setTimeout(() => setSuccessMessage(false), 2000);

    // Reset form only - keep modal open
    setFormData({
      ingredient: '',
      quantity: '',
      unit: '',
    });
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      ingredient: '',
      quantity: '',
      unit: '',
    });
    setSuccessMessage(false);
    onClose();
  };

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
            onClick={handleClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
          >
            {/* Modal Content */}
            <div className="relative bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg shadow-2xl w-full max-w-md border border-slate-700">
              {/* Close Button */}
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleClose}
                className="absolute top-4 right-4 z-50 bg-slate-700 hover:bg-slate-600 rounded-full p-2 shadow-lg transition"
                aria-label="Close modal"
              >
                <svg
                  className="w-6 h-6 text-white"
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
                <h1 className="text-3xl font-bold text-white mb-8">
                  Add Ingredient
                </h1>

                {/* Success Message */}
                <AnimatePresence>
                  {successMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.3 }}
                      className="mb-6 p-3 bg-green-600/20 border border-green-600/50 rounded-lg text-green-300 text-sm font-medium"
                    >
                      ✓ Ingredient added successfully!
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Form */}
                <div className="space-y-6">
                  {/* Ingredient Name */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-sm font-semibold text-gray-200">
                        Ingredient Name
                      </label>
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

                  {/* Quantity and Unit Row */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="grid grid-cols-3 gap-4"
                  >
                    {/* Quantity */}
                    <div className="col-span-1">
                      <label className="block text-sm font-semibold text-gray-200 mb-2">
                        Quantity
                      </label>
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

                    {/* Unit Dropdown */}
                    <div className="col-span-2">
                      <label className="block text-sm font-semibold text-gray-200 mb-2">
                        Unit
                      </label>
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

                  {/* Action Buttons */}
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
                      onClick={handleAddIngredient}
                      className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition font-semibold"
                    >
                      Add Ingredient
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