
import os

from enum import Enum

from pokemon_data import load_groups, load_types, pkmn_form


dest_dir = 'generated'


class alignment(Enum):
    LEFT = 0
    RIGHT = 1
    CENTER = 2

def generate_table(header: list[str], alignments: list[alignment], lines: list[list[str]]) -> list[str] :
    res = []
    max_sizes = []
    for i in range(len(header)) :
        max_sizes.append(max(len(header[i]), max(len(x[i]) for x in lines)))
    header_str = "|"
    for i, cell in enumerate(header) :
        header_str += f" {cell.ljust(max_sizes[i])} |"
    res.append(header_str)
    separator = "|"
    for i, align in enumerate(alignments) :
        separator += ("-" if align == alignment.RIGHT else ":")
        separator += "-" * max_sizes[i]
        separator += ("-" if align == alignment.LEFT else ":")
        separator += "|"
    res.append(separator)
    for line in lines :
        line_str = "|"
        for i, cell in enumerate(line) :
            line_str += " "
            if alignments[i] == alignment.RIGHT :
                line_str += cell.rjust(max_sizes[i])
            else:
                line_str += cell.ljust(max_sizes[i])
            line_str += " |"
        res.append(line_str)
    return res

def dump_table(lines: list[str], filepath: str):
    with open(filepath, 'w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')


common_spritesheet = 'common_pkmn_sprites'
shiny_spritesheet = 'shiny_pkmn_sprites'
types_spritesheet = 'type_sprites'

def sprite_for_form(form: pkmn_form, group_num: int, shiny: bool, spritesheet: bool) -> str :
    if spritesheet:
        sprites = shiny_spritesheet if shiny else common_spritesheet
        classes = f".pkmn-icon .n{group_num:04d}"
        if form.variant is not None :
            classes += f" .{form.variant}"
        res = f"![{form.names.en} sprite][{sprites}]{{{classes}}}"
        if form.gender_variant:
            res += f"![{form.names.en} female sprite][{sprites}]{{{classes} .female}}"
        return res
    shiny_name = 'shiny' if shiny else 'common'
    base_path = f"../sprites/{shiny_name}/icons/{group_num:04d}"
    if form.variant is not None :
        suffix = f"_{form.variant}.png"
    else:
        suffix = '.png'
    if not form.gender_variant:
        return f"![{form.names.en} sprite]({base_path}{suffix})"
    return f"![{form.names.en} male sprite]({base_path}_m{suffix}) ![{form.names.en} female sprite]({base_path}_f{suffix})"

def sprite_for_type(type: str, spritesheet: bool) -> str :
    if spritesheet:
        return f"![{type} type][{types_spritesheet}]{{.pkmn-type .icon .g3 .{type}}}"
    return f"![{type} type]"



def main():
    os.makedirs(dest_dir, exist_ok=True)

    insert_images=False
    use_spritesheets=False # With extended Markdown syntax to apply classes on elements

    pokemon_data = load_groups()

    header = ['N°']
    alignments = [alignment.CENTER]
    if insert_images :
        header.extend(['Common', 'Shiny'])
        alignments.extend([alignment.CENTER, alignment.CENTER])
    header.extend(['Name (EN)', 'Name (FR)', 'Type', 'Gen'])
    alignments.extend([alignment.LEFT, alignment.LEFT, alignment.CENTER, alignment.CENTER])

    lines = []

    for group in pokemon_data:
        for form in group.forms:
            line = [f"{group.number:04d}"]
            if insert_images:
                line.append(sprite_for_form(form, group.number, False, use_spritesheets))
                line.append(sprite_for_form(form, group.number, True, use_spritesheets))
            line.append(f"[{form.names.en}]({form.links.bulbapedia})")
            line.append(f"[{form.names.fr}]({form.links.pokepedia})")
            if insert_images:
                line.append(" ".join(sprite_for_type(x, use_spritesheets) for x in form.types))
            else:
                line.append(", ".join(form.types))
            line.append(str(form.gen))
            lines.append(line)

    # We use reference-style links for images to reduce the document size
    table = generate_table(header, alignments, lines)
    if insert_images:
        table.append('')
        if use_spritesheets:
            table.extend([
                f"[{common_spritesheet}]: ./spritesheets/common.png",
                f"[{shiny_spritesheet}]: ./spritesheets/shiny.png",
                f"[{types_spritesheet}]: ./spritesheets/type_icons_g3.png"
            ])
        else:
            for type in load_types().keys():
                table.append(f"[{type} type]: ../sprites/types/{type}/en/icon_g3.png")

    dump_table(table, os.path.join(dest_dir, 'pokemon.md'))

if __name__ == '__main__':
    main()
