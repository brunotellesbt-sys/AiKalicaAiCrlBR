"""Non-Water species that swim; do not equate a missing Water type with land."""
NAMES = ['SPECIES_AZURILL', 'SPECIES_QWILFISH_HISUI', 'SPECIES_OVERQWIL',
         'SPECIES_DRAGALGE', 'SPECIES_DHELMISE', 'SPECIES_CLOBBOPUS',
         'SPECIES_GRAPPLOCT', 'SPECIES_EISCUE_ICE', 'SPECIES_EISCUE_NOICE']


def aquatic_ids(catalog):
    return {int(i) for i, row in catalog.items()
            if 12 in row['types'] or row['name'] in NAMES}
