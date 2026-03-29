# Real MealDB-inspired fallback recipes with verified matching image URLs.
# Ingredient names are lightly normalized to fit this app's matching system.

FALLBACK_RECIPES = {
    "spicy arrabiata penne": {
        "pasta": "1 lb",
        "olive oil": "0.25 cup",
        "garlic": "3 clove",
        "canned tomato": "1 can",
        "chili": "0.5 tsp",
        "oregano": "0.5 tsp",
        "basil": "6 piece",
        "cheese": "1 tbsp",
        "image_url": "https://www.themealdb.com/images/media/meals/ustsqw1468250014.jpg",
        "description": "A spicy Italian pasta with tomato, garlic, basil, and chili.",
        "instructions": [
            "Boil the pasta until al dente.",
            "Heat olive oil and sauté the garlic briefly.",
            "Add canned tomato, chili, oregano, and seasoning to taste.",
            "Simmer the sauce for a few minutes, then stir in basil.",
            "Drain the pasta, toss with the sauce, and finish with cheese."
        ],
        "youtube_url": "https://www.youtube.com/watch?v=1IszT_guI08",
    },

    "chicken handi": {
        "chicken": "1.2 kg",
        "onion": "5 piece",
        "tomato": "2 piece",
        "garlic": "8 clove",
        "ginger": "1 tbsp",
        "oil": "0.25 cup",
        "yogurt": "1 cup",
        "cream": "0.75 cup",
        "chili": "2 piece",
        "image_url": "https://www.themealdb.com/images/media/meals/wyxwsp1486979827.jpg",
        "description": "A rich, creamy chicken curry with yogurt, cream, onion, and spices.",
        "instructions": [
            "Cook sliced onion in oil until deep golden, then remove and set aside.",
            "Cook garlic and tomato in the same pot until softened.",
            "Return the onion and add ginger, chili, and the chicken.",
            "Cook covered on medium-low heat until the chicken is nearly done.",
            "Stir in yogurt, then finish with cream and serve hot."
        ],
    },

    "beef rendang": {
        "beef": "1 lb",
        "oil": "5 tbsp",
        "cinnamon": "1 piece",
        "clove": "3 piece",
        "cardamom": "3 piece",
        "coconut cream": "1 cup",
        "water": "1 cup",
        "lime": "6 piece",
        "sugar": "1 tbsp",
        "image_url": "https://www.themealdb.com/images/media/meals/bc8v651619789840.jpg",
        "description": "A deeply flavored slow-cooked beef dish with warm spices and coconut cream.",
        "instructions": [
            "Make or finely chop a spice paste.",
            "Cook the spice paste in oil with cinnamon, cloves, and cardamom.",
            "Add beef and stir until coated and lightly cooked.",
            "Add coconut cream, water, lime, and sugar.",
            "Simmer slowly until the beef is tender and the sauce reduces."
        ],
    },

    "pancakes": {
        "flour": "100 g",
        "egg": "2",
        "milk": "300 ml",
        "oil": "1 tbsp",
        "salt": "1 tsp",
        "image_url": "https://www.themealdb.com/images/media/meals/rwuyqx1511383174.jpg",
        "description": "Classic simple pancakes made from flour, eggs, milk, oil, and salt.",
        "instructions": [
            "Whisk flour, eggs, milk, oil, and a pinch of salt into a smooth batter.",
            "Let the batter rest briefly if you want.",
            "Lightly oil a hot pan.",
            "Cook each pancake until golden on both sides.",
            "Serve warm with your choice of topping."
        ],
    },

    "chicken alfredo primavera": {
        "butter": "2 tbsp",
        "olive oil": "3 tbsp",
        "chicken": "5 piece",
        "broccoli": "1 piece",
        "mushroom": "8 oz",
        "pepper": "1 piece",
        "onion": "1 piece",
        "garlic": "3 clove",
        "milk": "0.5 cup",
        "cream": "0.5 cup",
        "cheese": "1 cup",
        "pasta": "12 oz",
        "image_url": "https://www.themealdb.com/images/media/meals/syqypv1486981727.jpg",
        "description": "Creamy chicken pasta with vegetables and parmesan-style cheese.",
        "instructions": [
            "Cook the chicken in butter and olive oil until done, then set aside.",
            "Boil pasta until al dente and reserve a little pasta water.",
            "Cook the vegetables in the same pan, then add garlic.",
            "Pour in milk and cream, then stir in cheese.",
            "Toss in the pasta and chicken and cook until coated."
        ],
    },

    "pad see ew": {
        "rice noodles": "180 g",
        "soy sauce": "2 tbsp",
        "oyster sauce": "2 tbsp",
        "vinegar": "2 tsp",
        "sugar": "2 tsp",
        "water": "2 tbsp",
        "oil": "2 tbsp",
        "garlic": "2 clove",
        "chicken": "1 cup",
        "egg": "1",
        "broccoli": "4 cup",
        "image_url": "https://www.themealdb.com/images/media/meals/uuuspp1468263334.jpg",
        "description": "A savory noodle stir-fry with chicken, egg, greens, and dark sauce.",
        "instructions": [
            "Mix the sauces, vinegar, sugar, and water together.",
            "Cook garlic in oil, then add chicken and the firm vegetable pieces.",
            "Push everything aside and scramble the egg in the pan.",
            "Add noodles, greens, and the sauce mixture.",
            "Toss everything together until the noodles are coated and hot."
        ],
    },

    "vegan lasagna": {
        "lentil": "1 cup",
        "carrot": "1 piece",
        "onion": "1 piece",
        "zucchini": "1 piece",
        "spinach": "150 g",
        "lasagna sheet": "10 piece",
        "butter": "35 g",
        "flour": "4 tbsp",
        "milk": "300 ml",
        "mustard": "1.5 tsp",
        "vinegar": "1 tsp",
        "image_url": "https://www.themealdb.com/images/media/meals/rvxxuy1468312893.jpg",
        "description": "A plant-based lasagna with lentils, vegetables, spinach, and a creamy sauce.",
        "instructions": [
            "Cook the vegetables until softened, then simmer with lentils.",
            "Blanch the spinach and set it aside.",
            "Cook the lasagna sheets until just tender.",
            "Make the sauce with butter, flour, milk, mustard, and vinegar.",
            "Layer everything in a baking dish and bake until hot and set."
        ],
    },

    "spaghetti bolognese": {
        "onion": "2 piece",
        "olive oil": "1 tbsp",
        "garlic": "1 clove",
        "beef": "500 g",
        "mushroom": "90 g",
        "oregano": "1 tsp",
        "canned tomato": "1 can",
        "beef stock": "300 ml",
        "tomato puree": "1 tbsp",
        "worcestershire sauce": "1 tbsp",
        "pasta": "350 g",
        "cheese": "1 tbsp",
        "image_url": "https://www.themealdb.com/images/media/meals/sutysw1468247559.jpg",
        "description": "A classic meat sauce pasta with tomato, beef, mushroom, and herbs.",
        "instructions": [
            "Cook onion in oil, then add garlic and beef until browned.",
            "Add mushroom and oregano and cook briefly.",
            "Stir in tomato, stock, puree, and Worcestershire sauce.",
            "Simmer until the sauce thickens and develops flavor.",
            "Serve the sauce over cooked pasta with cheese on top."
        ],
    },

    "teriyaki chicken casserole": {
        "soy sauce": "0.75 cup",
        "water": "0.5 cup",
        "brown sugar": "0.25 cup",
        "ginger": "0.5 tsp",
        "garlic": "0.5 tsp",
        "cornstarch": "4 tbsp",
        "chicken": "2 piece",
        "vegetable": "12 oz",
        "rice": "3 cup",
        "image_url": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg",
        "description": "A baked chicken-and-rice casserole coated in sweet savory teriyaki sauce.",
        "instructions": [
            "Make the teriyaki sauce with soy sauce, water, sugar, ginger, garlic, and cornstarch.",
            "Bake the chicken with some of the sauce until cooked through.",
            "Shred the chicken in the baking dish.",
            "Cook the vegetables and rice separately.",
            "Mix everything together with the remaining sauce and bake again briefly."
        ],
    },

    "chicken fried rice": {
        "chicken": "1 lb",
        "salt": "1 tsp",
        "oil": "3 tbsp",
        "egg": "3",
        "onion": "0.67 cup",
        "garlic": "2 clove",
        "ginger": "2 tsp",
        "carrot": "1 piece",
        "pea": "0.67 cup",
        "rice": "4 cup",
        "scallion": "2 piece",
        "soy sauce": "2.5 tbsp",
        "sesame oil": "1 tsp",
        "image_url": "https://www.themealdb.com/images/media/meals/wuyd2h1765655837.jpg",
        "description": "A wok-style fried rice with chicken, egg, vegetables, soy sauce, and sesame oil.",
        "instructions": [
            "Use day-old rice if possible so it stays separate in the pan.",
            "Cook the egg first and set it aside.",
            "Cook the chicken until done and remove it.",
            "Cook onion, garlic, ginger, carrot, and peas.",
            "Add rice, soy sauce, sesame oil, chicken, and egg, then stir-fry until hot."
        ],
    },
}