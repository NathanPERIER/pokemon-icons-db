
import os

from lxml import etree

from pokemon_data import load_groups


dest_dir = 'generated'

def dump_html(path: str, document: etree.ElementTree):
    etree.indent(document, space='    ')
    with open(path, 'wb') as f:
        f.write(b'<!doctype html>\n')
        f.write(etree.tostring(document, pretty_print=True, encoding='utf-8', method='html', xml_declaration=False))
        # document.write(f, encoding='utf-8', method='html', xml_declaration=False)


inline_styles = """
:root {
    font-family: sans-serif;
}
a {
    text-decoration: none;
}
code {
    background-color: #ebebeb;
    padding: 2px;
    border-radius: 4px;
}
table {
    border-collapse: collapse;
}
th, td {
    border: 1px solid black;
    padding-left: 4px;
    padding-right: 4px;
}
tr.group-start td {
    border-top-width: 2px;
}
td:nth-child(1),
td:nth-child(2),
tr.group-start td:nth-child(3),
td:nth-last-child(2),
td:nth-last-child(1) {
    text-align: center;
}
"""

def generate_document(table: etree.Element) -> etree.ElementTree:
    html = etree.Element('html', lang='en-GB')
    head = etree.SubElement(html, 'head')
    etree.SubElement(head, 'meta', charset='utf-8')
    etree.SubElement(head, 'title').text = 'Simple Pokédex test'
    etree.SubElement(head, 'link', rel='stylesheet', href="spritesheets/styles.css")
    etree.SubElement(head, 'style').text = inline_styles
    # <script src="script.js"></script>
    body = etree.SubElement(html, 'body')
    etree.SubElement(body, 'h1').text = "Simple Pokédex"
    body.append(table)
    return etree.ElementTree(html)

def insert_sprites(common_parent: etree.Element, shiny_parent: etree.Element, group_num: int, variant: str | None, female: bool):
    classes: list[str] = ['pkmn-icon', f"n{group_num:04d}"]
    if variant is not None:
        classes.append(variant)
    if female:
        classes.append('female')
    classes_str = " ".join(classes)
    common_parent.append(etree.Element('span', attrib={'class': classes_str}))
    shiny_parent.append(etree.Element('span', attrib={'class': f"{classes_str} shiny"}))


def main():
    os.makedirs(dest_dir, exist_ok=True)

    pokemon_data = load_groups()

    table = etree.Element('table', attrib={'id': 'pkmn-table'})
    header = etree.SubElement(table, 'tr')
    etree.SubElement(header, 'th').text = "N°"
    etree.SubElement(header, 'th').text = "Common"
    etree.SubElement(header, 'th').text = "Shiny"
    etree.SubElement(header, 'th').text = "Name (EN)"
    etree.SubElement(header, 'th').text = "Name (FR)"
    etree.SubElement(header, 'th').text = "Variant"
    etree.SubElement(header, 'th').text = "Gen"
    etree.SubElement(header, 'th').text = "Type"

    for group in pokemon_data:
        first = True
        for form in group.forms:
            line = etree.SubElement(table, 'tr')
            if first:
                line.attrib['class'] = 'group-start'
                etree.SubElement(line, 'td', rowspan=str(len(group.forms))).text = f"{group.number:04d}"
            icon_cell = etree.SubElement(line, 'td')
            shiny_cell = etree.SubElement(line, 'td')
            insert_sprites(icon_cell, shiny_cell, group.number, form.variant, False)
            if form.gender_variant: 
                insert_sprites(icon_cell, shiny_cell, group.number, form.variant, True)
            etree.SubElement(etree.SubElement(line, 'td'), 'a', href=form.links.bulbapedia).text = form.names.en
            etree.SubElement(etree.SubElement(line, 'td'), 'a', href=form.links.pokepedia).text = form.names.fr
            variant_cell = etree.SubElement(line, 'td')
            if form.variant is not None :
                etree.SubElement(variant_cell, 'code').text = form.variant
            etree.SubElement(line, 'td').text = str(form.gen)
            type_cell = etree.SubElement(line, 'td')
            for type in form.types :
                etree.SubElement(type_cell, 'span', attrib={'class': f"pkmn-type icon g3 {type}"})
            first = False

    dump_html(os.path.join(dest_dir, 'index.html'), generate_document(table))

if __name__ == '__main__':
    main()
