"""Reusable suggestion lists used by the flock, health, inventory, and breeding forms.

These values power the ``<datalist>`` / ``<select>`` helpers in the UI.
They are not written to the database unless the user submits a form, so farms
can still type their own item names, units, breeds, or parent tags.
"""

INVENTORY_ITEM_TYPES = [
    ('medicine', 'Medicine Cabinet'),
    ('feed', 'Feeds & Nutrition'),
    ('equipment', 'Equipment'),
    ('supply', 'Other Supplies'),
]

# Selective categories per inventory item type
MEDICINE_CATEGORIES = [
    ('Vaccine', 'Vaccine'),
    ('Dewormer', 'Dewormer'),
    ('Vitamin', 'Vitamin / Supplement'),
    ('Antibiotic', 'Antibiotic'),
    ('Treatment', 'Treatment / First aid'),
    ('Other', 'Other Medicine'),
]

FEED_CATEGORIES = [
    ('Chick Booster', 'Chick Booster (0-4 Weeks)'),
    ('Starter Feed', 'Starter Feed (1-3 Months)'),
    ('Grower Feed', 'Grower / Developer (4-7 Months)'),
    ('Maintenance Feed', 'Maintenance Feed'),
    ('Conditioning Feed', 'Conditioning Feed'),
    ('Grain Mix', 'Grain & Seed Mix'),
    ('Supplements', 'Supplements & Additives'),
    ('Other', 'Other Feed'),
]

EQUIPMENT_CATEGORIES = [
    ('Housing & Pens', 'Housing, Pens & Cages'),
    ('Feeding & Watering', 'Feeders & Waterers'),
    ('Brooder & Heating', 'Brooder & Heating Equipment'),
    ('Handling & Restraint', 'Tether Cords, Swivels & Ties'),
    ('Scales & Measurement', 'Scales & Measuring Tools'),
    ('Tools & Grooming', 'Tools, Grooming & Maintenance'),
    ('Other', 'Other Equipment'),
]

SUPPLY_CATEGORIES = [
    ('Bedding & Litter', 'Bedding & Wood Shavings'),
    ('Disinfectant & Sanitation', 'Disinfectants & Cleaning'),
    ('Identification', 'Leg Bands & Wing Bands'),
    ('Nesting & Incubation', 'Nesting Materials & Egg Trays'),
    ('Pest & Fly Control', 'Pest, Mite & Fly Control'),
    ('Packaging & Transport', 'Carry Boxes & Bags'),
    ('Other', 'Other Supplies'),
]

CATEGORIES_BY_TYPE = {
    'medicine': MEDICINE_CATEGORIES,
    'feed': FEED_CATEGORIES,
    'equipment': EQUIPMENT_CATEGORIES,
    'supply': SUPPLY_CATEGORIES,
}

# Selective units per inventory item type
MEDICINE_UNITS = [
    'ml', 'g', 'kg', 'tablet', 'capsule', 'vial', 'ampule', 'bottle', 'dose', 'sachet', 'drop',
]

FEED_UNITS = [
    'sack (50kg)', 'bag (25kg)', 'sack', 'bag', 'kg', 'g', 'lbs',
]

EQUIPMENT_UNITS = [
    'pcs', 'unit', 'set', 'pair', 'pack',
]

SUPPLY_UNITS = [
    'pack', 'bottle', 'roll', 'box', 'pcs', 'sack', 'can', 'pail',
]

UNITS_BY_TYPE = {
    'medicine': MEDICINE_UNITS,
    'feed': FEED_UNITS,
    'equipment': EQUIPMENT_UNITS,
    'supply': SUPPLY_UNITS,
}

# Common gamefowl medicines and treatments, grouped by the cabinet category.
COMMON_MEDICINES = [
    # Vaccines
    {'name': 'Newcastle Disease Vaccine (ND)', 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    {'name': 'Gumboro Vaccine (IBD)', 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    {'name': 'Fowl Pox Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    {'name': 'Infectious Bronchitis Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    {'name': 'Fowl Cholera Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    {'name': 'Avian Influenza Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    {'name': "Marek's Disease Vaccine", 'category': 'Vaccine', 'unit': 'vial', 'record_type': 'Vaccination'},
    # Dewormers
    {'name': 'Piperazine', 'category': 'Dewormer', 'unit': 'ml', 'record_type': 'Deworming'},
    {'name': 'Albendazole', 'category': 'Dewormer', 'unit': 'tablet', 'record_type': 'Deworming'},
    {'name': 'Fenbendazole', 'category': 'Dewormer', 'unit': 'g', 'record_type': 'Deworming'},
    {'name': 'Levamisole', 'category': 'Dewormer', 'unit': 'ml', 'record_type': 'Deworming'},
    {'name': 'Ivermectin 1%', 'category': 'Dewormer', 'unit': 'ml', 'record_type': 'Deworming'},
    # Vitamins and supplements
    {'name': 'Vitamin A', 'category': 'Vitamin', 'unit': 'tablet', 'record_type': 'Vitamin'},
    {'name': 'Vitamin D3', 'category': 'Vitamin', 'unit': 'ml', 'record_type': 'Vitamin'},
    {'name': 'Vitamin E (Wheat Germ)', 'category': 'Vitamin', 'unit': 'capsule', 'record_type': 'Vitamin'},
    {'name': 'B-Complex Vitamin Injectable', 'category': 'Vitamin', 'unit': 'ml', 'record_type': 'Vitamin'},
    {'name': 'Multivitamins + Minerals Powder', 'category': 'Vitamin', 'unit': 'sachet', 'record_type': 'Vitamin'},
    {'name': 'Electrolytes Powder', 'category': 'Vitamin', 'unit': 'sachet', 'record_type': 'Vitamin'},
    {'name': 'Liver Tonic Drops', 'category': 'Vitamin', 'unit': 'bottle', 'record_type': 'Vitamin'},
    # Antibiotics
    {'name': 'Amoxicillin Powder', 'category': 'Antibiotic', 'unit': 'g', 'record_type': 'Treatment'},
    {'name': 'Oxytetracycline LA', 'category': 'Antibiotic', 'unit': 'ml', 'record_type': 'Treatment'},
    {'name': 'Tylosin Tartrate', 'category': 'Antibiotic', 'unit': 'g', 'record_type': 'Treatment'},
    {'name': 'Enrofloxacin 10%', 'category': 'Antibiotic', 'unit': 'ml', 'record_type': 'Treatment'},
    {'name': 'Doxycycline + Colistin', 'category': 'Antibiotic', 'unit': 'sachet', 'record_type': 'Treatment'},
    # First aid and treatments
    {'name': 'Povidone-Iodine 10%', 'category': 'Treatment', 'unit': 'bottle', 'record_type': 'Treatment'},
    {'name': 'Betadine Wound Solution', 'category': 'Treatment', 'unit': 'bottle', 'record_type': 'Treatment'},
    {'name': 'Hydrogen Peroxide 3%', 'category': 'Treatment', 'unit': 'bottle', 'record_type': 'Treatment'},
    {'name': 'Terramycin Wound Spray', 'category': 'Treatment', 'unit': 'bottle', 'record_type': 'Treatment'},
    {'name': 'Epsom Salt', 'category': 'Treatment', 'unit': 'kg', 'record_type': 'Treatment'},
]

# Common gamefowl feeds and nutrition options
COMMON_FEEDS = [
    {'name': 'Chick Booster Crumble (0-4 Weeks)', 'category': 'Chick Booster', 'unit': 'sack (50kg)'},
    {'name': 'Stag Developer 4+ (Stag Feeds)', 'category': 'Grower Feed', 'unit': 'sack (50kg)'},
    {'name': 'Chick Starter Pellets', 'category': 'Starter Feed', 'unit': 'sack (50kg)'},
    {'name': 'Maintenance Grain & Pellet Mix', 'category': 'Maintenance Feed', 'unit': 'sack (50kg)'},
    {'name': 'Thunderbird Platinum Conditioning Pellets', 'category': 'Conditioning Feed', 'unit': 'sack (50kg)'},
    {'name': 'Integra 3000 Maintenance Pellets', 'category': 'Maintenance Feed', 'unit': 'sack (50kg)'},
    {'name': 'Hardened Red Corn / Yellow Corn', 'category': 'Grain Mix', 'unit': 'sack (50kg)'},
    {'name': 'Pigeon Feed Grain Mix', 'category': 'Grain Mix', 'unit': 'sack (50kg)'},
    {'name': 'Oat Groats & Barley Grain', 'category': 'Grain Mix', 'unit': 'kg'},
    {'name': 'Calf Manna High-Protein Booster', 'category': 'Supplements', 'unit': 'bag (25kg)'},
    {'name': 'Green Pea & Safflower Seed Mix', 'category': 'Grain Mix', 'unit': 'kg'},
    {'name': 'Concentrated Amino Acid Powder', 'category': 'Supplements', 'unit': 'pack'},
]

# Common equipment options
COMMON_EQUIPMENT = [
    {'name': 'Heavy Duty Tie-Cord (Nylon Braided 3ft)', 'category': 'Handling & Restraint', 'unit': 'pcs'},
    {'name': 'Cord Ball-Bearing Swivel & Clip', 'category': 'Handling & Restraint', 'unit': 'set'},
    {'name': 'Soft Leather Leg Strap for Tie-Cord', 'category': 'Handling & Restraint', 'unit': 'pcs'},
    {'name': 'Galvanized Hanging Feeder (2kg)', 'category': 'Feeding & Watering', 'unit': 'pcs'},
    {'name': 'Automatic Bell Waterer / Drinker Cup', 'category': 'Feeding & Watering', 'unit': 'pcs'},
    {'name': 'Collapsible Scratch Pen (8x8 ft)', 'category': 'Housing & Pens', 'unit': 'unit'},
    {'name': 'Polyethylene Flying Pen Netting (50m)', 'category': 'Housing & Pens', 'unit': 'roll'},
    {'name': 'Infrared Brooder Heat Lamp (150W)', 'category': 'Brooder & Heating', 'unit': 'pcs'},
    {'name': 'Ceramic Heat Emitter Bulb (100W)', 'category': 'Brooder & Heating', 'unit': 'pcs'},
    {'name': 'Digital Hanging Scale with Hook (50kg)', 'category': 'Scales & Measurement', 'unit': 'unit'},
    {'name': 'Precision Gram Scale (0.1g - 500g)', 'category': 'Scales & Measurement', 'unit': 'unit'},
    {'name': 'Gamefowl Single Transport / Carry Box', 'category': 'Housing & Pens', 'unit': 'pcs'},
    {'name': 'Dubbing Shears (Stainless Steel Curved)', 'category': 'Tools & Grooming', 'unit': 'pcs'},
    {'name': 'Leather Sparring Gloves (Set of 4)', 'category': 'Tools & Grooming', 'unit': 'set'},
]

# Common other supplies options
COMMON_SUPPLIES = [
    {'name': 'Kiln-Dried Pine Wood Shavings', 'category': 'Bedding & Litter', 'unit': 'sack'},
    {'name': 'Virkon S Broad-Spectrum Disinfectant', 'category': 'Disinfectant & Sanitation', 'unit': 'pack'},
    {'name': 'Chlorine Granules / Tablets (1kg)', 'category': 'Disinfectant & Sanitation', 'unit': 'bottle'},
    {'name': 'Agricultural Hydrated Lime Powder (25kg)', 'category': 'Disinfectant & Sanitation', 'unit': 'sack'},
    {'name': 'Numbered Aluminum Leg Bands (1-100)', 'category': 'Identification', 'unit': 'pack'},
    {'name': 'Tamper-Proof Wing Bands (Pack of 100)', 'category': 'Identification', 'unit': 'pack'},
    {'name': 'Wing Band Pliers / Applicator', 'category': 'Identification', 'unit': 'pcs'},
    {'name': 'Golden Malrin Fly Bait Granules', 'category': 'Pest & Fly Control', 'unit': 'can'},
    {'name': 'Red Mite & Lice Dust Powder (Sevin 5%)', 'category': 'Pest & Fly Control', 'unit': 'can'},
    {'name': 'Clean Rice Straw / Nesting Hay', 'category': 'Nesting & Incubation', 'unit': 'sack'},
    {'name': 'Plastic 30-Egg Incubator Trays', 'category': 'Nesting & Incubation', 'unit': 'pcs'},
    {'name': 'Vet Wrap Self-Adhesive Elastic Bandage', 'category': 'Packaging & Transport', 'unit': 'roll'},
]

SUGGESTIONS_BY_TYPE = {
    'medicine': COMMON_MEDICINES,
    'feed': COMMON_FEEDS,
    'equipment': COMMON_EQUIPMENT,
    'supply': COMMON_SUPPLIES,
}

# Popular gamefowl breeds / bloodlines used as suggestions when adding a bird.
COMMON_BREEDS = [
    'Sweater', 'Kelso', 'Hatch', 'Roundhead', 'Grey', 'Radio', 'Butcher',
    'Albany', 'Muff', 'Morgan Whitehackle', 'Law Grey', 'Asil', 'Shamo',
    'Brazilian', 'Thai', 'Pure Kelso', 'Pure Sweater',
]

# Map a medicine cabinet category to the closest health record type.
CATEGORY_RECORD_TYPES = {
    'Vaccine': 'Vaccination',
    'Dewormer': 'Deworming',
    'Vitamin': 'Vitamin',
    'Antibiotic': 'Treatment',
    'Treatment': 'Treatment',
    'Other': 'Treatment',
}


def record_type_for_category(category):
    """Return the health record type that matches a medicine category."""
    return CATEGORY_RECORD_TYPES.get(category, 'Treatment')
