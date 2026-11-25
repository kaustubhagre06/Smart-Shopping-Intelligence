"""
Deterministic dataset & SVG product artwork generator for Smart Shopping Intelligence System.
Generates:
  1. data/products.json (36 curated products across 6 categories)
  2. data/transactions.csv (1,200 realistic shopping basket transactions)
  3. static/images/products/<slug>.svg (crisp custom vector illustrations for all 36 products)
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "products")

PRODUCTS = [
    # Bakery & Breakfast
    {
        "id": 1,
        "name": "Bread",
        "slug": "bread",
        "category": "Bakery & Breakfast",
        "price": 3.49,
        "unit": "500g loaf",
        "rating": 4.8,
        "badge": "Best Seller",
        "featured": True,
        "color": "#F59E0B",
        "bg": "#FEF3C7",
        "icon": "loaf",
        "description": "Freshly baked artisan sourdough loaf with a golden crust and soft, airy crumb. Ideal for morning toast and sandwiches."
    },
    {
        "id": 2,
        "name": "Croissant",
        "slug": "croissant",
        "category": "Bakery & Breakfast",
        "price": 2.99,
        "unit": "pack of 4",
        "rating": 4.7,
        "badge": "Fresh Daily",
        "featured": False,
        "color": "#D97706",
        "bg": "#FDE68A",
        "icon": "pastry",
        "description": "Flaky, laminated French-style butter croissants baked crisp every morning."
    },
    {
        "id": 3,
        "name": "Oatmeal",
        "slug": "oatmeal",
        "category": "Bakery & Breakfast",
        "price": 4.99,
        "unit": "900g canister",
        "rating": 4.6,
        "badge": "High Fiber",
        "featured": False,
        "color": "#B45309",
        "bg": "#FEF3C7",
        "icon": "grain",
        "description": "100% whole-grain rolled oats for hearty breakfast bowls, overnight oats, and healthy baking."
    },
    {
        "id": 4,
        "name": "Cereal",
        "slug": "cereal",
        "category": "Bakery & Breakfast",
        "price": 4.79,
        "unit": "450g box",
        "rating": 4.5,
        "badge": "Family Pack",
        "featured": False,
        "color": "#EA580C",
        "bg": "#FFEDD5",
        "icon": "bowl",
        "description": "Crunchy honey-toasted multigrain flakes fortified with essential vitamins and iron."
    },
    {
        "id": 5,
        "name": "Peanut Butter",
        "slug": "peanut-butter",
        "category": "Bakery & Breakfast",
        "price": 5.49,
        "unit": "450g jar",
        "rating": 4.8,
        "badge": "Protein Rich",
        "featured": False,
        "color": "#92400E",
        "bg": "#FDE68A",
        "icon": "jar",
        "description": "Creamy roasted peanut spread crafted with sea salt and zero hydrogenated oils."
    },
    {
        "id": 6,
        "name": "Strawberry Jam",
        "slug": "strawberry-jam",
        "category": "Bakery & Breakfast",
        "price": 4.19,
        "unit": "340g jar",
        "rating": 4.7,
        "badge": "All Natural",
        "featured": False,
        "color": "#E11D48",
        "bg": "#FFE4E6",
        "icon": "jar",
        "description": "Sun-ripened whole strawberry preserves cooked in small batches for vibrant fruit flavor."
    },

    # Dairy & Eggs
    {
        "id": 7,
        "name": "Milk",
        "slug": "milk",
        "category": "Dairy & Eggs",
        "price": 3.79,
        "unit": "1L bottle",
        "rating": 4.9,
        "badge": "Organic",
        "featured": True,
        "color": "#2563EB",
        "bg": "#DBEAFE",
        "icon": "bottle",
        "description": "Farm-fresh pasture-raised whole milk rich in calcium and natural Vitamin D."
    },
    {
        "id": 8,
        "name": "Butter",
        "slug": "butter",
        "category": "Dairy & Eggs",
        "price": 4.29,
        "unit": "250g block",
        "rating": 4.8,
        "badge": "Grass-Fed",
        "featured": True,
        "color": "#EAB308",
        "bg": "#FEF9C3",
        "icon": "block",
        "description": "Rich, creamy grass-fed salted butter perfect for spreading on warm bread or gourmet cooking."
    },
    {
        "id": 9,
        "name": "Eggs",
        "slug": "eggs",
        "category": "Dairy & Eggs",
        "price": 4.89,
        "unit": "12 large eggs",
        "rating": 4.9,
        "badge": "Free Range",
        "featured": False,
        "color": "#D97706",
        "bg": "#FEF3C7",
        "icon": "eggs",
        "description": "Grade-A free-range brown eggs with deep golden yolks from pasture-roaming hens."
    },
    {
        "id": 10,
        "name": "Cheddar Cheese",
        "slug": "cheddar-cheese",
        "category": "Dairy & Eggs",
        "price": 5.99,
        "unit": "250g block",
        "rating": 4.7,
        "badge": "Aged 12 Mo",
        "featured": False,
        "color": "#F59E0B",
        "bg": "#FEF3C7",
        "icon": "cheese",
        "description": "Sharp, savory aged cheddar cheese ideal for melts, snacking, and nacho platters."
    },
    {
        "id": 11,
        "name": "Greek Yogurt",
        "slug": "greek-yogurt",
        "category": "Dairy & Eggs",
        "price": 4.49,
        "unit": "500g tub",
        "rating": 4.8,
        "badge": "High Protein",
        "featured": False,
        "color": "#0284C7",
        "bg": "#E0F2FE",
        "icon": "tub",
        "description": "Thick, velvety strained Greek yogurt packed with probiotics and 18g protein per serving."
    },
    {
        "id": 12,
        "name": "Parmesan",
        "slug": "parmesan",
        "category": "Dairy & Eggs",
        "price": 6.49,
        "unit": "180g wedge",
        "rating": 4.8,
        "badge": "Imported",
        "featured": False,
        "color": "#CA8A04",
        "bg": "#FEF9C3",
        "icon": "cheese",
        "description": "Authentic 24-month aged Parmigiano-style cheese wedge with nutty crystalline richness."
    },

    # Fresh Produce
    {
        "id": 13,
        "name": "Bananas",
        "slug": "bananas",
        "category": "Fresh Produce",
        "price": 1.99,
        "unit": "1kg bunch",
        "rating": 4.7,
        "badge": "Fresh Pick",
        "featured": False,
        "color": "#EAB308",
        "bg": "#FEF9C3",
        "icon": "fruit",
        "description": "Sweet, naturally ripened Cavendish bananas ideal for smoothies, oatmeal, and energy snacks."
    },
    {
        "id": 14,
        "name": "Strawberries",
        "slug": "strawberries",
        "category": "Fresh Produce",
        "price": 4.99,
        "unit": "400g punnet",
        "rating": 4.8,
        "badge": "Seasonal",
        "featured": False,
        "color": "#E11D48",
        "bg": "#FFE4E6",
        "icon": "berry",
        "description": "Juicy hand-picked red strawberries bursting with sweetness for yogurt parfaits and desserts."
    },
    {
        "id": 15,
        "name": "Avocado",
        "slug": "avocado",
        "category": "Fresh Produce",
        "price": 2.49,
        "unit": "pack of 2",
        "rating": 4.7,
        "badge": "Ripe & Ready",
        "featured": True,
        "color": "#16A34A",
        "bg": "#DCFCE7",
        "icon": "avocado",
        "description": "Creamy Hass avocados rich in healthy monounsaturated fats—great for toast, salads, and dips."
    },
    {
        "id": 16,
        "name": "Tomatoes",
        "slug": "tomatoes",
        "category": "Fresh Produce",
        "price": 3.29,
        "unit": "500g vine pack",
        "rating": 4.6,
        "badge": "Vine Ripened",
        "featured": False,
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "icon": "tomato",
        "description": "Aromatic vine-ripened heirloom tomatoes suited for crisp salads, sauces, and bruschetta."
    },
    {
        "id": 17,
        "name": "Spinach",
        "slug": "spinach",
        "category": "Fresh Produce",
        "price": 3.49,
        "unit": "250g bag",
        "rating": 4.6,
        "badge": "Triple Washed",
        "featured": False,
        "color": "#15803D",
        "bg": "#DCFCE7",
        "icon": "leaf",
        "description": "Tender baby spinach leaves ready for fresh salads, omelets, and green smoothies."
    },
    {
        "id": 18,
        "name": "Garlic",
        "slug": "garlic",
        "category": "Fresh Produce",
        "price": 1.49,
        "unit": "3-bulb net",
        "rating": 4.7,
        "badge": "Aromatic",
        "featured": False,
        "color": "#78716C",
        "bg": "#F5F5F4",
        "icon": "bulb",
        "description": "Bold, fragrant hardneck garlic bulbs essential for Mediterranean pasta and savory dishes."
    },

    # Pantry & Cooking
    {
        "id": 19,
        "name": "Pasta",
        "slug": "pasta",
        "category": "Pantry & Cooking",
        "price": 2.79,
        "unit": "500g pack",
        "rating": 4.8,
        "badge": "Artisan Bronze",
        "featured": True,
        "color": "#D97706",
        "bg": "#FEF3C7",
        "icon": "pasta",
        "description": "Bronze-die extruded Italian durum wheat penne crafted to hold rich sauces effortlessly."
    },
    {
        "id": 20,
        "name": "Pasta Sauce",
        "slug": "pasta-sauce",
        "category": "Pantry & Cooking",
        "price": 4.59,
        "unit": "680g jar",
        "rating": 4.8,
        "badge": "Chef Recipe",
        "featured": False,
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "icon": "jar",
        "description": "Slow-simmered San Marzano tomato marinara infused with sweet basil and roasted garlic."
    },
    {
        "id": 21,
        "name": "Olive Oil",
        "slug": "olive-oil",
        "category": "Pantry & Cooking",
        "price": 9.99,
        "unit": "750ml bottle",
        "rating": 4.9,
        "badge": "Cold Pressed",
        "featured": False,
        "color": "#65A30D",
        "bg": "#ECFCCB",
        "icon": "bottle",
        "description": "First cold-pressed extra virgin olive oil with vibrant peppery notes for dressings and sauteing."
    },
    {
        "id": 22,
        "name": "Basmati Rice",
        "slug": "basmati-rice",
        "category": "Pantry & Cooking",
        "price": 6.99,
        "unit": "2kg bag",
        "rating": 4.8,
        "badge": "Aged Grain",
        "featured": False,
        "color": "#A16207",
        "bg": "#FEF3C7",
        "icon": "grain",
        "description": "Long-grain aromatic Himalayan basmati rice that cooks light, fluffy, and non-sticky."
    },
    {
        "id": 23,
        "name": "Soy Sauce",
        "slug": "soy-sauce",
        "category": "Pantry & Cooking",
        "price": 3.89,
        "unit": "500ml bottle",
        "rating": 4.7,
        "badge": "Naturally Brewed",
        "featured": False,
        "color": "#44403C",
        "bg": "#E7E5E4",
        "icon": "bottle",
        "description": "Traditionally fermented umami-rich soy sauce for stir-fries, marinades, and rice bowls."
    },
    {
        "id": 24,
        "name": "Honey",
        "slug": "honey",
        "category": "Pantry & Cooking",
        "price": 7.49,
        "unit": "350g jar",
        "rating": 4.9,
        "badge": "Raw Wildflower",
        "featured": False,
        "color": "#D97706",
        "bg": "#FEF3C7",
        "icon": "jar",
        "description": "Unfiltered raw wildflower honey with floral sweetness for tea, yogurt, and oatmeal."
    },

    # Beverages & Snacks
    {
        "id": 25,
        "name": "Coffee",
        "slug": "coffee",
        "category": "Beverages & Snacks",
        "price": 11.99,
        "unit": "340g roast",
        "rating": 4.9,
        "badge": "Top Rated",
        "featured": True,
        "color": "#78350F",
        "bg": "#FDE68A",
        "icon": "coffee",
        "description": "Single-origin medium-roast 100% Arabica coffee beans with rich cocoa and caramel notes."
    },
    {
        "id": 26,
        "name": "Green Tea",
        "slug": "green-tea",
        "category": "Beverages & Snacks",
        "price": 5.29,
        "unit": "40 tea bags",
        "rating": 4.7,
        "badge": "Antioxidant",
        "featured": False,
        "color": "#16A34A",
        "bg": "#DCFCE7",
        "icon": "tea",
        "description": "Delicate steamed Japanese-style sencha green tea leaves for calm, focused mornings."
    },
    {
        "id": 27,
        "name": "Orange Juice",
        "slug": "orange-juice",
        "category": "Beverages & Snacks",
        "price": 4.79,
        "unit": "1L carafe",
        "rating": 4.7,
        "badge": "100% Pressed",
        "featured": False,
        "color": "#EA580C",
        "bg": "#FFEDD5",
        "icon": "bottle",
        "description": "Cold-pressed Valencia orange juice packed with natural Vitamin C and zero added sugar."
    },
    {
        "id": 28,
        "name": "Sparkling Water",
        "slug": "sparkling-water",
        "category": "Beverages & Snacks",
        "price": 3.99,
        "unit": "6-pack cans",
        "rating": 4.6,
        "badge": "Zero Sugar",
        "featured": False,
        "color": "#0EA5E9",
        "bg": "#E0F2FE",
        "icon": "can",
        "description": "Crisp mineral sparkling water infused with natural Meyer lemon essence."
    },
    {
        "id": 29,
        "name": "Tortilla Chips",
        "slug": "tortilla-chips",
        "category": "Beverages & Snacks",
        "price": 3.99,
        "unit": "300g bag",
        "rating": 4.7,
        "badge": "Stone Ground",
        "featured": False,
        "color": "#CA8A04",
        "bg": "#FEF9C3",
        "icon": "bag",
        "description": "Crispy stone-ground white corn tortilla chips lightly dusted with sea salt."
    },
    {
        "id": 30,
        "name": "Salsa Dip",
        "slug": "salsa-dip",
        "category": "Beverages & Snacks",
        "price": 4.29,
        "unit": "420g jar",
        "rating": 4.7,
        "badge": "Medium Kick",
        "featured": False,
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "icon": "jar",
        "description": "Chunky fire-roasted tomato salsa blended with jalapenos, cilantro, and fresh lime."
    },

    # Treats & Household
    {
        "id": 31,
        "name": "Dark Chocolate",
        "slug": "dark-chocolate",
        "category": "Treats & Household",
        "price": 3.79,
        "unit": "100g bar",
        "rating": 4.9,
        "badge": "72% Cacao",
        "featured": False,
        "color": "#57534E",
        "bg": "#E7E5E4",
        "icon": "chocolate",
        "description": "Velvety Belgian 72% single-origin dark chocolate bar with subtle roasted espresso notes."
    },
    {
        "id": 32,
        "name": "Potato Chips",
        "slug": "potato-chips",
        "category": "Treats & Household",
        "price": 3.49,
        "unit": "220g bag",
        "rating": 4.6,
        "badge": "Kettle Cooked",
        "featured": False,
        "color": "#D97706",
        "bg": "#FEF3C7",
        "icon": "bag",
        "description": "Thick-cut kettle-cooked sea salt & cracked black pepper potato chips."
    },
    {
        "id": 33,
        "name": "Hand Soap",
        "slug": "hand-soap",
        "category": "Treats & Household",
        "price": 4.49,
        "unit": "350ml pump",
        "rating": 4.8,
        "badge": "Plant Based",
        "featured": False,
        "color": "#0D9488",
        "bg": "#CCFBF1",
        "icon": "pump",
        "description": "Botanical aloe & eucalyptus foaming hand cleanser gentle on skin and tough on germs."
    },
    {
        "id": 34,
        "name": "Paper Towels",
        "slug": "paper-towels",
        "category": "Treats & Household",
        "price": 6.99,
        "unit": "4 mega rolls",
        "rating": 4.7,
        "badge": "Ultra Absorb",
        "featured": False,
        "color": "#4F46E5",
        "bg": "#E0E7FF",
        "icon": "roll",
        "description": "Two-ply quilted bamboo-blend paper towels engineered for everyday kitchen cleanups."
    },
    {
        "id": 35,
        "name": "Dish Liquid",
        "slug": "dish-liquid",
        "category": "Treats & Household",
        "price": 4.19,
        "unit": "500ml bottle",
        "rating": 4.7,
        "badge": "Eco Formula",
        "featured": False,
        "color": "#0891B2",
        "bg": "#CFFAFE",
        "icon": "bottle",
        "description": "Concentrated citrus-powered biodegradable dishwashing liquid that cuts grease fast."
    },
    {
        "id": 36,
        "name": "Laundry Pods",
        "slug": "laundry-pods",
        "category": "Treats & Household",
        "price": 10.99,
        "unit": "32 pods tub",
        "rating": 4.8,
        "badge": "Deep Clean",
        "featured": False,
        "color": "#7C3AED",
        "bg": "#EDE9FE",
        "icon": "tub",
        "description": "High-efficiency 3-in-1 enzyme laundry detergent pods safe for cold water cycles."
    },
]


def _svg_shape(icon: str, color: str) -> str:
    """Return crisp vector artwork matching each product silhouette."""
    shapes = {
        "loaf": f'<path d="M52 108c0-26 20-44 48-44s48 18 48 44v16a10 10 0 0 1-10 10H62a10 10 0 0 1-10-10v-16z" fill="{color}"/><path d="M74 72c6 6 10 12 10 18M100 68c6 6 10 12 10 18M124 72c5 6 8 11 8 16" stroke="#FFFBEB" stroke-width="4" stroke-linecap="round"/>',
        "pastry": f'<path d="M54 114c10-28 30-42 46-42s36 14 46 42c-12 10-28 14-46 14s-34-4-46-14z" fill="{color}"/><path d="M84 74l-6 46M116 74l6 46" stroke="#FFFBEB" stroke-width="3.5" stroke-linecap="round"/>',
        "bottle": f'<rect x="86" y="48" width="28" height="14" rx="4" fill="{color}" opacity="0.85"/><path d="M84 64h32l10 20v50a10 10 0 0 1-10 10H84a10 10 0 0 1-10-10V84l10-20z" fill="{color}"/><rect x="80" y="92" width="40" height="28" rx="4" fill="#FFFFFF" opacity="0.85"/>',
        "block": f'<path d="M54 94l42-26 50 18-42 28-50-20z" fill="{color}"/><path d="M54 94v26l50 20v-26l-50-20z" fill="{color}" opacity="0.82"/><path d="M104 114v26l42-28V86l-42 28z" fill="{color}" opacity="0.68"/>',
        "eggs": f'<rect x="52" y="88" width="96" height="44" rx="10" fill="#D6D3D1"/><ellipse cx="76" cy="88" rx="14" ry="18" fill="{color}"/><ellipse cx="100" cy="84" rx="14" ry="18" fill="#FDE68A"/><ellipse cx="124" cy="88" rx="14" ry="18" fill="{color}"/>',
        "cheese": f'<path d="M54 118l88-46 6 46H54z" fill="{color}"/><path d="M54 118h94v18H54z" fill="{color}" opacity="0.82"/><circle cx="96" cy="108" r="6" fill="#FFFBEB"/><circle cx="122" cy="102" r="8" fill="#FFFBEB"/><circle cx="114" cy="126" r="4" fill="#FFFBEB"/>',
        "jar": f'<rect x="76" y="52" width="48" height="14" rx="5" fill="#475569"/><rect x="66" y="68" width="68" height="72" rx="16" fill="{color}"/><rect x="74" y="88" width="52" height="32" rx="6" fill="#FFFFFF" opacity="0.88"/>',
        "tub": f'<rect x="60" y="60" width="80" height="14" rx="6" fill="{color}"/><path d="M66 74h68l-8 64a8 8 0 0 1-8 7H82a8 8 0 0 1-8-7l-8-64z" fill="{color}" opacity="0.86"/><rect x="76" y="92" width="48" height="26" rx="5" fill="#FFFFFF" opacity="0.88"/>',
        "bowl": f'<path d="M56 96h88c0 24-18 42-44 42s-44-18-44-42z" fill="{color}"/><circle cx="82" cy="84" r="10" fill="#FBBF24"/><circle cx="102" cy="80" r="11" fill="#F59E0B"/><circle cx="120" cy="86" r="9" fill="#FBBF24"/>',
        "grain": f'<rect x="64" y="56" width="72" height="86" rx="14" fill="{color}"/><path d="M100 78c-12 10-12 28 0 38 12-10 12-28 0-38z" fill="#FFFBEB" opacity="0.9"/>',
        "fruit": f'<path d="M62 122c18 16 58 8 76-36 6-14-4-24-12-14-12 22-36 36-60 36-8 0-12 8-4 14z" fill="{color}"/><path d="M126 68l6-10" stroke="#78350F" stroke-width="5" stroke-linecap="round"/>',
        "berry": f'<path d="M100 138c-22-10-34-34-30-54 3-14 16-22 30-22s27 8 30 22c4 20-8 44-30 54z" fill="{color}"/><path d="M84 62l16 10 16-10-10-10H94l-10 10z" fill="#16A34A"/><circle cx="88" cy="92" r="2.5" fill="#FFE4E6"/><circle cx="104" cy="86" r="2.5" fill="#FFE4E6"/><circle cx="110" cy="106" r="2.5" fill="#FFE4E6"/><circle cx="92" cy="114" r="2.5" fill="#FFE4E6"/>',
        "avocado": f'<path d="M100 54c-18 0-32 24-32 48 0 22 14 38 32 38s32-16 32-38c0-24-14-48-32-48z" fill="{color}"/><path d="M100 62c-13 0-24 20-24 40 0 17 11 30 24 30s24-13 24-30c0-20-11-40-24-40z" fill="#BEF264"/><circle cx="100" cy="108" r="14" fill="#78350F"/>',
        "tomato": f'<circle cx="100" cy="102" r="36" fill="{color}"/><path d="M86 68l14 8 14-8-10-10H96l-10 10z" fill="#16A34A"/><ellipse cx="86" cy="88" rx="8" ry="5" transform="rotate(-30 86 88)" fill="#FFFFFF" opacity="0.35"/>',
        "leaf": f'<path d="M64 132c0-44 28-72 72-74-2 44-30 74-72 74z" fill="{color}"/><path d="M66 130L124 72" stroke="#DCFCE7" stroke-width="4" stroke-linecap="round"/>',
        "bulb": f'<path d="M100 56c-6 14-32 26-32 50 0 18 14 30 32 30s32-12 32-30c0-24-26-36-32-50z" fill="#E7E5E4" stroke="{color}" stroke-width="3"/><path d="M100 62v74M84 84c-4 14-4 32 4 48M116 84c4 14 4 32-4 48" stroke="{color}" stroke-width="2.5" fill="none"/>',
        "pasta": f'<rect x="64" y="60" width="72" height="80" rx="10" fill="{color}"/><rect x="74" y="80" width="52" height="40" rx="6" fill="#FFFBEB"/><path d="M82 90l12 20M96 90l12 20M110 90l10 16" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
        "coffee": f'<rect x="64" y="54" width="72" height="86" rx="12" fill="{color}"/><circle cx="100" cy="96" r="18" fill="#FEF3C7"/><path d="M100 84c-5 6-5 18 0 24" stroke="{color}" stroke-width="3" stroke-linecap="round"/>',
        "tea": f'<rect x="58" y="68" width="84" height="66" rx="12" fill="{color}"/><path d="M100 80c-12 10-12 26 0 36 12-10 12-26 0-36z" fill="#DCFCE7"/>',
        "can": f'<rect x="74" y="56" width="52" height="82" rx="10" fill="{color}"/><rect x="74" y="84" width="52" height="24" fill="#FFFFFF" opacity="0.85"/><ellipse cx="100" cy="56" rx="24" ry="5" fill="#BAE6FD"/>',
        "bag": f'<path d="M64 60h72l-6 80H70l-6-80z" fill="{color}"/><rect x="76" y="84" width="48" height="28" rx="6" fill="#FFFFFF" opacity="0.85"/>',
        "chocolate": f'<rect x="66" y="54" width="68" height="88" rx="8" fill="{color}"/><path d="M66 84h68M66 112h68M100 54v88" stroke="#A8A29E" stroke-width="3"/><path d="M66 106l68-14v50H66v-36z" fill="#4F46E5" opacity="0.88"/>',
        "pump": f'<path d="M94 52h24v8H94zM100 60v12" stroke="#334155" stroke-width="5" stroke-linecap="round"/><rect x="74" y="72" width="52" height="68" rx="14" fill="{color}"/><rect x="82" y="92" width="36" height="26" rx="5" fill="#FFFFFF" opacity="0.85"/>',
        "roll": f'<rect x="62" y="64" width="76" height="72" rx="10" fill="{color}" opacity="0.9"/><ellipse cx="100" cy="64" rx="38" ry="12" fill="#FFFFFF" stroke="{color}" stroke-width="3"/><ellipse cx="100" cy="64" rx="12" ry="4" fill="#94A3B8"/>',
    }
    return shapes.get(icon, shapes["jar"])


def generate_product_svgs() -> None:
    os.makedirs(IMG_DIR, exist_ok=True)
    for item in PRODUCTS:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="g-{item['slug']}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{item['bg']}"/>
      <stop offset="100%" stop-color="#FFFFFF"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="28" fill="url(#g-{item['slug']})"/>
  <circle cx="158" cy="42" r="24" fill="{item['color']}" opacity="0.12"/>
  <circle cx="40" cy="158" r="18" fill="{item['color']}" opacity="0.10"/>
  {_svg_shape(item['icon'], item['color'])}
</svg>'''
        out_path = os.path.join(IMG_DIR, f"{item['slug']}.svg")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)


def generate_transactions_csv(num_transactions: int = 1200) -> list[dict]:
    """
    Generate realistic market-basket transactions with clear co-purchase patterns
    for Apriori association rule mining.
    """
    rng = random.Random(42)

    # Weighted shopping personas / basket archetypes
    archetypes = [
        # Classic breakfast: Bread <-> Butter <-> Eggs <-> Milk
        (0.18, ["Bread", "Butter", "Eggs", "Milk"], ["Coffee", "Orange Juice"]),
        # Toast & spreads: Bread <-> Peanut Butter <-> Strawberry Jam
        (0.10, ["Bread", "Peanut Butter", "Strawberry Jam"], ["Milk", "Bananas"]),
        # Cafe morning: Coffee <-> Milk <-> Croissant <-> Butter
        (0.11, ["Coffee", "Milk", "Croissant"], ["Butter", "Dark Chocolate"]),
        # Italian pasta night: Pasta <-> Pasta Sauce <-> Parmesan <-> Garlic <-> Olive Oil
        (0.14, ["Pasta", "Pasta Sauce", "Parmesan", "Garlic"], ["Olive Oil", "Spinach"]),
        # Healthy bowl / smoothie: Greek Yogurt <-> Strawberries <-> Bananas <-> Honey <-> Oatmeal
        (0.11, ["Greek Yogurt", "Strawberries", "Bananas", "Honey"], ["Oatmeal", "Cereal"]),
        # Taco / snack platter: Tortilla Chips <-> Salsa Dip <-> Avocado <-> Cheddar Cheese
        (0.10, ["Tortilla Chips", "Salsa Dip", "Avocado"], ["Cheddar Cheese", "Sparkling Water"]),
        # Fresh salad: Spinach <-> Tomatoes <-> Avocado <-> Olive Oil
        (0.08, ["Spinach", "Tomatoes", "Avocado", "Olive Oil"], ["Eggs", "Bread"]),
        # Asian stir-fry: Basmati Rice <-> Soy Sauce <-> Garlic
        (0.06, ["Basmati Rice", "Soy Sauce", "Garlic"], ["Spinach", "Green Tea"]),
        # Tea & relaxation: Green Tea <-> Honey <-> Dark Chocolate
        (0.06, ["Green Tea", "Honey", "Dark Chocolate"], ["Oatmeal", "Bananas"]),
        # Movie & household restock
        (0.06, ["Potato Chips", "Sparkling Water", "Dark Chocolate"], ["Paper Towels", "Hand Soap"]),
    ]

    weights = [a[0] for a in archetypes]
    all_names = [p["name"] for p in PRODUCTS]
    household = ["Hand Soap", "Paper Towels", "Dish Liquid", "Laundry Pods"]

    base_date = datetime(2026, 9, 1, 9, 0, 0)
    rows = []

    for idx in range(1, num_transactions + 1):
        core, optional = rng.choices([(a[1], a[2]) for a in archetypes], weights=weights, k=1)[0]
        basket = set()

        # Include most of the core bundle so support & confidence are realistic
        for item in core:
            if rng.random() < 0.80:
                basket.add(item)
        if len(basket) < 2:
            basket.update(core[:2])

        # Add optional complementary items
        for item in optional:
            if rng.random() < 0.42:
                basket.add(item)

        # Occasional household co-purchase cluster
        if rng.random() < 0.16:
            hh = rng.sample(household, k=rng.randint(2, 3))
            basket.update(hh)

        # Small random cross-category noise
        if rng.random() < 0.25:
            basket.add(rng.choice(all_names))

        tx_time = base_date + timedelta(hours=idx * 1.4, minutes=rng.randint(0, 59))
        rows.append(
            {
                "transaction_id": f"TXN-{10000 + idx}",
                "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                "items": ",".join(sorted(basket)),
            }
        )

    csv_path = os.path.join(DATA_DIR, "transactions.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["transaction_id", "timestamp", "items"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    products_out = []
    for p in PRODUCTS:
        entry = dict(p)
        entry["image_path"] = f"/static/images/products/{p['slug']}.svg"
        products_out.append(entry)

    with open(os.path.join(DATA_DIR, "products.json"), "w", encoding="utf-8") as f:
        json.dump(products_out, f, indent=2)

    generate_product_svgs()
    rows = generate_transactions_csv(1200)
    print(f"Generated {len(products_out)} products, SVGs, and {len(rows)} transactions.")


if __name__ == "__main__":
    main()
