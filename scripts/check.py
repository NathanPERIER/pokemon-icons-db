
import os
import sys

from pokemon_data import load_groups, load_types, pkmn_group, pkmn_form


class error_logger :
    def __init__(self):
        self.has_error: bool = False
        self.print_num: bool = True
        self.num: int = 0

    def start_group(self, number: int):
        self.num = number
        self.print_num = False

    def error(self, message: str):
        self.has_error = True
        if not self.print_num :
            print(f"===== Group #{self.num:04d} ==========================")
            self.print_num = True
        print(f"ERR: {message}")
    
    def ok(self) -> bool :
        return not self.has_error


def check_sprite_files(filename: str, logger: error_logger):
    common_icon_path = os.path.join('sprites/common/icons', filename)
    shiny_icon_path = os.path.join('sprites/shiny/icons', filename)
    if not os.path.isfile(common_icon_path) :
        logger.error(f"Common icon not found in {common_icon_path}")
    if not os.path.isfile(shiny_icon_path) :
        logger.error(f"Shiny icon not found in {shiny_icon_path}")

def check_pokemon_sprites(group: pkmn_group, form: pkmn_form, logger: error_logger):
    group_id = f"{group.number:04d}"
    if form.gender_variant :
        sprite_files = [f"{group_id}_f", f"{group_id}_m"]
    else:
        sprite_files = [f"{group_id}"]
    if form.variant is not None :
        sprite_files = [f"{x}_{form.variant}" for x in sprite_files]
    sprite_files = [f"{x}.png" for x in sprite_files]
    for filename in sprite_files:
        check_sprite_files(filename, logger)

def check_pokemon_groups(pokemon_data: list[pkmn_group], logger: error_logger):
    last_number: int | None = None
    all_groups: dict[int, pkmn_group] = {}
    for group in pokemon_data:
        logger.start_group(group.number)
        if group.number in all_groups :
            logger.error(f"Group {group.number} was found several times)")
        if last_number is not None and last_number+1 != group.number :
            logger.error(f"Group {group.number} is misplaced (previous is {last_number})")
        last_number = group.number
        all_groups[group.number] = group
        known_variants: list[str | None] = []
        for form in group.forms :
            if form.variant is None and form.derives is not None :
                logger.error('Default form cannot be derived from another form')
            if form.variant in known_variants :
                logger.error(f"Duplicate variant {form.variant}")
            known_variants.append(form.variant)
        if None not in known_variants and group.common_names is None :
            logger.error('Groups without a default variant must define common names')
        if any(x is None for x in known_variants) :
            if group.forms[0].variant is not None :
                logger.error('Null variant is not the first entry in the form list')
        else:
            if len(group.forms) < 2 :
                logger.error(f"Group with only one form should not have a variant (found {group.forms[0].variant})")
            if group.forms[0].derives is not None :
                logger.error(f"First form in group (with variant {group.forms[0].variant}) cannot derive other forms")
            if group.forms[0].is_temporary() :
                logger.error(f"First form in group (with variant {group.forms[0].variant}) cannot be battle-only")
    for group in pokemon_data:
        logger.start_group(group.number)
        pre_evolution: pkmn_group | None = None
        if group.evolves_from is not None :
            if group.evolves_from in all_groups :
                pre_evolution = all_groups[group.evolves_from]
            else:
                logger.error(f"Group {group.number} evolves from unknown group {group.evolves_from}")
        for form in group.forms :
            check_pokemon_sprites(group, form, logger)
            if form.evolution_variants is not None :
                if form.derives is not None :
                    logger.error(f"Found evolution variant {form.evolution_variants} for derived group")
                if group.evolves_from is None :
                    logger.error(f"Found evolution variant {form.evolution_variants} for non-evolving group")
                    continue
                if pre_evolution is not None :
                    for evolution_variants in form.evolution_variants :
                        pre_form = pre_evolution.find_form(evolution_variants)
                        if pre_form is None :
                            logger.error(f"Evolution variant {evolution_variants} does not exist in pre-evolution group {pre_evolution.number}")
                        if pre_form.derives is not None :
                            logger.error(f"Evolution variant {evolution_variants} in pre-evolution group {pre_evolution.number} refers to a derived form")
            elif pre_evolution is not None :
                pre_form = pre_evolution.find_form(form.variant)
                if pre_form is None:
                    if form.variant is None :
                        logger.error(f"Pre-evolution group {pre_evolution.number} does not have a default variant to evolve")
                        continue
                    else:
                        pre_form = pre_evolution.find_form(None)
                        if pre_form is None :
                            logger.error(f"Pre-evolution group {pre_evolution.number} does not have a {form.variant} variant to evolve, nor a default variant")
                            continue
                if pre_form.derives is not None :
                    if pre_form.variant is None :
                        logger.error(f"Default evolution variant in pre-evolution group {pre_evolution.number} refers to a derived form")
                    else:
                        logger.error(f"Evolution variant {pre_form.variant} in pre-evolution group {pre_evolution.number} refers to a derived form")
            if form.derives is None and form.gender_ratio is None :
                logger.error(f"Missing gender ratio for non-derived form {form.variant}")
            if form.gender_variant and (form.gender_ratio is None or not form.gender_ratio.is_mixed()) :
                logger.error(f"Found gender variant for form {form.variant} with non-mixed gender ratio {form.gender_ratio}")
    for group in pokemon_data :
        logger.start_group(group.number)
        for form in group.forms :
            if form.derives is not None :
                for derived_variant in form.derives.from_variants :
                    if derived_variant == form.variant :
                        logger.error(f"Variant {form.variant} derives from itself")
                        continue
                    derived_form = group.find_form(derived_variant)
                    if derived_form is None :
                        if derived_variant is None :
                            logger.error(f"Variant {form.variant} derives from non-existing default variant")
                        else:
                            logger.error(f"Variant {form.variant} derives from non-existing variant {derived_variant}")
                        continue
                    if derived_form.is_temporary() and not form.is_temporary() :
                        logger.error(f"Permanent variant {form.variant} derives from battle-only variant {derived_variant}")

def main() -> int :
    logger = error_logger()

    try:
        type_data = load_types()
        print('Types schema validation OK')
    except Exception as e:
        print(f"Type data does not match the provided schema: {e}")
        return 1

    try:
        pokemon_data = load_groups()
        print('Pokémon schema validation OK')
    except Exception as e:
        print(f"Pokémon data does not match the provided schema: {e}")
        return 1

    check_pokemon_groups(pokemon_data, logger)

    if logger.ok() :
        print(f"Checked {len(pokemon_data)} groups => all OK")
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
