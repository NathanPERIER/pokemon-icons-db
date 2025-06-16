
import os
import math

from PIL import Image

from pokemon_data import load_groups

dest_dir = './generated/spritesheets'

sprites_base_dir = 'sprites'
unknown_sprite_path = os.path.join(sprites_base_dir, 'unknown.png')
common_sprites_dir = os.path.join(sprites_base_dir, 'common/icons')
shiny_sprites_dir = os.path.join(sprites_base_dir, 'shiny/icons')

sprite_class = '.pkmn-icon'
sprite_size = (68, 56) # width, height


phi = (1 + 5 ** 0.5) / 2
class spritesheet:
    def __init__(self, capacity: int, sprite_size: tuple[int, int]):
        self._capacity = capacity
        self._sprite_width = sprite_size[0]
        self._sprite_height = sprite_size[1]
        self._grid_width = math.ceil(math.sqrt((self._capacity * self._sprite_height) / (self._sprite_width * phi)))
        self._grid_height = math.ceil(self._capacity / self._grid_width)
        self._current_x = 0
        self._current_y = 0
        self._im = Image.new('RGBA', (self._grid_width * self._sprite_width, self._grid_height * self._sprite_height))

    def add_sprite(self, sprite_path: str) -> tuple[int, int] :
        if self._current_x >= self._grid_width :
            self._current_x = 0
            self._current_y += 1
        if self._current_y >= self._grid_height :
            raise RuntimeError('Spritesheet exceeded capacity')
        res = (self._current_x, self._current_y)
        offset = (self._sprite_width * self._current_x, self._sprite_height * self._current_y)
        with Image.open(sprite_path) as sprite:
            if sprite.size != (self._sprite_width, self._sprite_height) :
                raise RuntimeError(f"Sprite at {sprite_path} has dimensions {sprite.size}, expected {(self._sprite_width, self._sprite_height)}")
            self._im.paste(sprite, offset)
        self._current_x += 1
        return res

    def write(self, filepath: str):
        self._im.save(filepath)


def main():
    os.makedirs(dest_dir, exist_ok=True)

    pokemon_data = load_groups()

    # Associate sprites (filenames) with CSS classes
    sprites: dict[str, list[str]] = {}
    for group in pokemon_data:
        first = True
        group_css_class = f"{sprite_class}.n{group.number:04d}"
        for form in group.forms:
            sprite_name = f"{group.number:04d}"
            female_sprite_name: str | None = None
            if form.gender_variant:
                female_sprite_name = f"{sprite_name}_f"
                sprite_name += "_m"
            if form.variant is not None :
                sprite_name += f"_{form.variant}"
                if female_sprite_name is not None :
                    female_sprite_name += f"_{form.variant}"
            css_classes = []
            female_css_classes = []
            if first:
                # First variant is either None or representative of the whole group
                css_classes.append(group_css_class)
                if female_sprite_name is not None :
                    female_css_classes.append(f"{group_css_class}.female")
            if form.variant is not None :
                # None variant (if any) is always first, so we can just manage all the other cases here
                css_classes.append(f"{group_css_class}.{form.variant}")
                if female_sprite_name is not None :
                    female_css_classes.append(f"{group_css_class}.female.{form.variant}")
            sprites[sprite_name] = css_classes
            if female_sprite_name is not None :
                sprites[female_sprite_name] = female_css_classes
            first = False

    stylesheet: list[str] = [
        f"{sprite_class} {{ " +
            "display: inline-block; " +
            f"width: {sprite_size[0]}px; " +
            f"height: {sprite_size[1]}px; " +
            "--psprite-x: 0; " +
            "--psprite-y: 0; " +
            "background: url('common.png'); " +
            f"background-position: calc(-1 * var(--psprite-x) * {sprite_size[0]}px) calc(-1 * var(--psprite-y) * {sprite_size[1]}px); " +
            "image-rendering: pixelated; " +
            "image-rendering: -moz-crisp-edges; " +
            "margin-left: -12px; " +
            "margin-right: -12px; " +
            "margin-top: -16px; " +
        "}",
        f"{sprite_class}.shiny {{ background-image: url('shiny.png'); }}"
    ]
    
    common_spritesheet = spritesheet(len(sprites), sprite_size)
    shiny_spritesheet = spritesheet(len(sprites), sprite_size)
    common_spritesheet.add_sprite(unknown_sprite_path)
    shiny_spritesheet.add_sprite(unknown_sprite_path)

    for filename, css_classes in sprites.items() :
        offset = common_spritesheet.add_sprite(os.path.join(common_sprites_dir, f"{filename}.png"))
        shiny_spritesheet.add_sprite(os.path.join(shiny_sprites_dir, f"{filename}.png"))
        css_classes_str = ", ".join(css_classes)
        stylesheet.append(f"{css_classes_str} {{ --psprite-x: {offset[0]}; --psprite-y: {offset[1]}; }}")

    common_spritesheet.write(os.path.join(dest_dir, 'common.png'))
    shiny_spritesheet.write(os.path.join(dest_dir, 'shiny.png'))
    with open(os.path.join(dest_dir, 'styles.css'), 'w') as f:
        f.write("\n".join(stylesheet))
    

if __name__ == '__main__':
    main()
