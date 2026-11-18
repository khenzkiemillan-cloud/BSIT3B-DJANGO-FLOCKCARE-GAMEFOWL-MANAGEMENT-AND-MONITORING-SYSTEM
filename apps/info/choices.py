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
    {'name': 'Newcastle Disease Vaccine (ND)', 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '180.00', 'record_type': 'Vaccination'},
    {'name': 'Gumboro Vaccine (IBD)', 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '210.00', 'record_type': 'Vaccination'},
    {'name': 'Fowl Pox Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '195.00', 'record_type': 'Vaccination'},
    {'name': 'Infectious Bronchitis Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '220.00', 'record_type': 'Vaccination'},
    {'name': 'Fowl Cholera Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '230.00', 'record_type': 'Vaccination'},
    {'name': 'Avian Influenza Vaccine', 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '250.00', 'record_type': 'Vaccination'},
    {'name': "Marek's Disease Vaccine", 'category': 'Vaccine', 'unit': 'vial', 'default_cost': '280.00', 'record_type': 'Vaccination'},
    # Dewormers
    {'name': 'Piperazine', 'category': 'Dewormer', 'unit': 'ml', 'default_cost': '95.00', 'record_type': 'Deworming'},
    {'name': 'Albendazole', 'category': 'Dewormer', 'unit': 'tablet', 'default_cost': '15.00', 'record_type': 'Deworming'},
    {'name': 'Fenbendazole', 'category': 'Dewormer', 'unit': 'g', 'default_cost': '45.00', 'record_type': 'Deworming'},
    {'name': 'Levamisole', 'category': 'Dewormer', 'unit': 'ml', 'default_cost': '120.00', 'record_type': 'Deworming'},
    {'name': 'Ivermectin 1%', 'category': 'Dewormer', 'unit': 'ml', 'default_cost': '160.00', 'record_type': 'Deworming'},
    # Vitamins and supplements
    {'name': 'Vitamin A', 'category': 'Vitamin', 'unit': 'tablet', 'default_cost': '12.00', 'record_type': 'Vitamin'},
    {'name': 'Vitamin D3', 'category': 'Vitamin', 'unit': 'ml', 'default_cost': '85.00', 'record_type': 'Vitamin'},
    {'name': 'Vitamin E (Wheat Germ)', 'category': 'Vitamin', 'unit': 'capsule', 'default_cost': '18.00', 'record_type': 'Vitamin'},
    {'name': 'B-Complex Vitamin Injectable', 'category': 'Vitamin', 'unit': 'ml', 'default_cost': '95.00', 'record_type': 'Vitamin'},
    {'name': 'Multivitamins + Minerals Powder', 'category': 'Vitamin', 'unit': 'sachet', 'default_cost': '35.00', 'record_type': 'Vitamin'},
    {'name': 'Electrolytes Powder', 'category': 'Vitamin', 'unit': 'sachet', 'default_cost': '25.00', 'record_type': 'Vitamin'},
    {'name': 'Liver Tonic Drops', 'category': 'Vitamin', 'unit': 'bottle', 'default_cost': '140.00', 'record_type': 'Vitamin'},
    # Antibiotics
    {'name': 'Amoxicillin Powder', 'category': 'Antibiotic', 'unit': 'g', 'default_cost': '50.00', 'record_type': 'Treatment'},
    {'name': 'Oxytetracycline LA', 'category': 'Antibiotic', 'unit': 'ml', 'default_cost': '110.00', 'record_type': 'Treatment'},
    {'name': 'Tylosin Tartrate', 'category': 'Antibiotic', 'unit': 'g', 'default_cost': '75.00', 'record_type': 'Treatment'},
    {'name': 'Enrofloxacin 10%', 'category': 'Antibiotic', 'unit': 'ml', 'default_cost': '130.00', 'record_type': 'Treatment'},
    {'name': 'Doxycycline + Colistin', 'category': 'Antibiotic', 'unit': 'sachet', 'default_cost': '45.00', 'record_type': 'Treatment'},
    # First aid and treatments
    {'name': 'Povidone-Iodine 10%', 'category': 'Treatment', 'unit': 'bottle', 'default_cost': '120.00', 'record_type': 'Treatment'},
    {'name': 'Betadine Wound Solution', 'category': 'Treatment', 'unit': 'bottle', 'default_cost': '145.00', 'record_type': 'Treatment'},
    {'name': 'Hydrogen Peroxide 3%', 'category': 'Treatment', 'unit': 'bottle', 'default_cost': '45.00', 'record_type': 'Treatment'},
    {'name': 'Terramycin Wound Spray', 'category': 'Treatment', 'unit': 'bottle', 'default_cost': '260.00', 'record_type': 'Treatment'},
    {'name': 'Epsom Salt', 'category': 'Treatment', 'unit': 'kg', 'default_cost': '60.00', 'record_type': 'Treatment'},
]

# Common gamefowl feeds and nutrition options
COMMON_FEEDS = [
    {'name': 'Chick Booster Crumble (0-4 Weeks)', 'category': 'Chick Booster', 'unit': 'sack (50kg)', 'default_cost': '2150.00'},
    {'name': 'Stag Developer 4+ (Stag Feeds)', 'category': 'Grower Feed', 'unit': 'sack (50kg)', 'default_cost': '2250.00'},
    {'name': 'Chick Starter Pellets', 'category': 'Starter Feed', 'unit': 'sack (50kg)', 'default_cost': '2100.00'},
    {'name': 'Maintenance Grain & Pellet Mix', 'category': 'Maintenance Feed', 'unit': 'sack (50kg)', 'default_cost': '1950.00'},
    {'name': 'Thunderbird Platinum Conditioning Pellets', 'category': 'Conditioning Feed', 'unit': 'sack (50kg)', 'default_cost': '2480.00'},
    {'name': 'Integra 3000 Maintenance Pellets', 'category': 'Maintenance Feed', 'unit': 'sack (50kg)', 'default_cost': '2050.00'},
    {'name': 'Hardened Red Corn / Yellow Corn', 'category': 'Grain Mix', 'unit': 'sack (50kg)', 'default_cost': '1650.00'},
    {'name': 'Pigeon Feed Grain Mix', 'category': 'Grain Mix', 'unit': 'sack (50kg)', 'default_cost': '2300.00'},
    {'name': 'Oat Groats & Barley Grain', 'category': 'Grain Mix', 'unit': 'kg', 'default_cost': '85.00'},
    {'name': 'Calf Manna High-Protein Booster', 'category': 'Supplements', 'unit': 'bag (25kg)', 'default_cost': '1850.00'},
    {'name': 'Green Pea & Safflower Seed Mix', 'category': 'Grain Mix', 'unit': 'kg', 'default_cost': '95.00'},
    {'name': 'Concentrated Amino Acid Powder', 'category': 'Supplements', 'unit': 'pack', 'default_cost': '320.00'},
]

# Common equipment options
COMMON_EQUIPMENT = [
    {'name': 'Heavy Duty Tie-Cord (Nylon Braided 3ft)', 'category': 'Handling & Restraint', 'unit': 'pcs', 'default_cost': '65.00'},
    {'name': 'Cord Ball-Bearing Swivel & Clip', 'category': 'Handling & Restraint', 'unit': 'set', 'default_cost': '35.00'},
    {'name': 'Soft Leather Leg Strap for Tie-Cord', 'category': 'Handling & Restraint', 'unit': 'pcs', 'default_cost': '45.00'},
    {'name': 'Galvanized Hanging Feeder (2kg)', 'category': 'Feeding & Watering', 'unit': 'pcs', 'default_cost': '180.00'},
    {'name': 'Automatic Bell Waterer / Drinker Cup', 'category': 'Feeding & Watering', 'unit': 'pcs', 'default_cost': '95.00'},
    {'name': 'Collapsible Scratch Pen (8x8 ft)', 'category': 'Housing & Pens', 'unit': 'unit', 'default_cost': '3200.00'},
    {'name': 'Polyethylene Flying Pen Netting (50m)', 'category': 'Housing & Pens', 'unit': 'roll', 'default_cost': '1850.00'},
    {'name': 'Infrared Brooder Heat Lamp (150W)', 'category': 'Brooder & Heating', 'unit': 'pcs', 'default_cost': '290.00'},
    {'name': 'Ceramic Heat Emitter Bulb (100W)', 'category': 'Brooder & Heating', 'unit': 'pcs', 'default_cost': '350.00'},
    {'name': 'Digital Hanging Scale with Hook (50kg)', 'category': 'Scales & Measurement', 'unit': 'unit', 'default_cost': '450.00'},
    {'name': 'Precision Gram Scale (0.1g - 500g)', 'category': 'Scales & Measurement', 'unit': 'unit', 'default_cost': '380.00'},
    {'name': 'Gamefowl Single Transport / Carry Box', 'category': 'Housing & Pens', 'unit': 'pcs', 'default_cost': '280.00'},
    {'name': 'Dubbing Shears (Stainless Steel Curved)', 'category': 'Tools & Grooming', 'unit': 'pcs', 'default_cost': '220.00'},
    {'name': 'Leather Sparring Gloves (Set of 4)', 'category': 'Tools & Grooming', 'unit': 'set', 'default_cost': '480.00'},
]

# Common other supplies options
COMMON_SUPPLIES = [
    {'name': 'Kiln-Dried Pine Wood Shavings', 'category': 'Bedding & Litter', 'unit': 'sack', 'default_cost': '120.00'},
    {'name': 'Virkon S Broad-Spectrum Disinfectant', 'category': 'Disinfectant & Sanitation', 'unit': 'pack', 'default_cost': '420.00'},
    {'name': 'Chlorine Granules / Tablets (1kg)', 'category': 'Disinfectant & Sanitation', 'unit': 'bottle', 'default_cost': '280.00'},
    {'name': 'Agricultural Hydrated Lime Powder (25kg)', 'category': 'Disinfectant & Sanitation', 'unit': 'sack', 'default_cost': '240.00'},
    {'name': 'Numbered Aluminum Leg Bands (1-100)', 'category': 'Identification', 'unit': 'pack', 'default_cost': '350.00'},
    {'name': 'Tamper-Proof Wing Bands (Pack of 100)', 'category': 'Identification', 'unit': 'pack', 'default_cost': '380.00'},
    {'name': 'Wing Band Pliers / Applicator', 'category': 'Identification', 'unit': 'pcs', 'default_cost': '290.00'},
    {'name': 'Golden Malrin Fly Bait Granules', 'category': 'Pest & Fly Control', 'unit': 'can', 'default_cost': '360.00'},
    {'name': 'Red Mite & Lice Dust Powder (Sevin 5%)', 'category': 'Pest & Fly Control', 'unit': 'can', 'default_cost': '180.00'},
    {'name': 'Clean Rice Straw / Nesting Hay', 'category': 'Nesting & Incubation', 'unit': 'sack', 'default_cost': '80.00'},
    {'name': 'Plastic 30-Egg Incubator Trays', 'category': 'Nesting & Incubation', 'unit': 'pcs', 'default_cost': '75.00'},
    {'name': 'Vet Wrap Self-Adhesive Elastic Bandage', 'category': 'Packaging & Transport', 'unit': 'roll', 'default_cost': '45.00'},
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
