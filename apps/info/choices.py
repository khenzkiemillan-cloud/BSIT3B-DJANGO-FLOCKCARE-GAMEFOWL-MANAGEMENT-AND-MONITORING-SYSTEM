"""Reusable suggestion lists used by the health, medicine, and breeding forms.

These values only power the ``<datalist>`` / ``<select>`` helpers in the UI.
They are not written to the database unless the user submits a form, so farms
can still type their own medicine names, units, breeds, or parent tags.
"""

# Common gamefowl medicines and treatments, grouped by the cabinet category.
COMMON_MEDICINES = [
    # Vaccines
    {'name': 'Newcastle Disease Vaccine (ND)', 'category': 'Vaccine', 'record_type': 'Vaccination'},
    {'name': 'Gumboro Vaccine (IBD)', 'category': 'Vaccine', 'record_type': 'Vaccination'},
    {'name': 'Fowl Pox Vaccine', 'category': 'Vaccine', 'record_type': 'Vaccination'},
    {'name': 'Infectious Bronchitis Vaccine', 'category': 'Vaccine', 'record_type': 'Vaccination'},
    {'name': 'Fowl Cholera Vaccine', 'category': 'Vaccine', 'record_type': 'Vaccination'},
    {'name': 'Avian Influenza Vaccine', 'category': 'Vaccine', 'record_type': 'Vaccination'},
    {'name': "Marek's Disease Vaccine", 'category': 'Vaccine', 'record_type': 'Vaccination'},
    # Dewormers
    {'name': 'Piperazine', 'category': 'Dewormer', 'record_type': 'Deworming'},
    {'name': 'Albendazole', 'category': 'Dewormer', 'record_type': 'Deworming'},
    {'name': 'Fenbendazole', 'category': 'Dewormer', 'record_type': 'Deworming'},
    {'name': 'Levamisole', 'category': 'Dewormer', 'record_type': 'Deworming'},
    {'name': 'Ivermectin', 'category': 'Dewormer', 'record_type': 'Deworming'},
    # Vitamins and supplements
    {'name': 'Vitamin A', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    {'name': 'Vitamin D3', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    {'name': 'Vitamin E', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    {'name': 'B-Complex Vitamin', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    {'name': 'Multivitamins', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    {'name': 'Electrolytes', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    {'name': 'Liver Tonic', 'category': 'Vitamin', 'record_type': 'Vitamin'},
    # Antibiotics
    {'name': 'Amoxicillin', 'category': 'Antibiotic', 'record_type': 'Treatment'},
    {'name': 'Oxytetracycline', 'category': 'Antibiotic', 'record_type': 'Treatment'},
    {'name': 'Tylosin', 'category': 'Antibiotic', 'record_type': 'Treatment'},
    {'name': 'Enrofloxacin', 'category': 'Antibiotic', 'record_type': 'Treatment'},
    {'name': 'Doxycycline', 'category': 'Antibiotic', 'record_type': 'Treatment'},
    # First aid and treatments
    {'name': 'Povidone-Iodine', 'category': 'Treatment', 'record_type': 'Treatment'},
    {'name': 'Betadine', 'category': 'Treatment', 'record_type': 'Treatment'},
    {'name': 'Hydrogen Peroxide', 'category': 'Treatment', 'record_type': 'Treatment'},
    {'name': 'Terramycin Wound Spray', 'category': 'Treatment', 'record_type': 'Treatment'},
    {'name': 'Epsom Salt', 'category': 'Treatment', 'record_type': 'Treatment'},
]

# Units commonly used in the medicine cabinet.
MEDICINE_UNITS = [
    'ml', 'g', 'kg', 'tablet', 'capsule', 'sachet', 'bottle', 'dose', 'drop',
]

# Popular gamefowl breeds / bloodlines used as suggestions when adding a bird.
COMMON_BREEDS = [
    'Sweater', 'Kelso', 'Hatch', 'Roundhead', 'Grey', 'Radio', 'Butcher',
    'Albany', 'Muff', 'Morgan Whitehackle', 'Law Grey', 'Asil', 'Shamo',
    'Brazilian', 'Thai', 'Pure Kelso', 'Pure Sweater',
]

# Common conditioning programs / regimens used to get a bird fight-ready.
CONDITIONING_PROGRAMS = [
    'Roadwork', 'Sparring', 'Feed control', 'Free range', 'Cage rest',
    'Water work', 'Combined program',
]

# Common feed / diet plans offered as quick picks while conditioning a bird.
# Users can still choose "Custom" and type their own plan.
CONDITIONING_FEED_PLANS = [
    'High-protein pellets, twice daily',
    'Mixed grains & seeds, twice daily',
    'Corn, oats & barley mix',
    'Booster mash with vitamins',
    'Light feed — controlled ration',
    'Free-range forage + supplement',
    'Fight-ready conditioning mix',
    'Recovery diet with electrolytes',
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
