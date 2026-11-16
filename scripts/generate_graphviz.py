
import os
import sys

from collections import deque

from pokemon_data import load_groups, load_types


dest_dir = './generated'


class form_node:
    def __init__(self, graph_id: str, name: str, colours: list[str], temporary: bool):
        self.graph_id = graph_id
        self.name = name
        self.colours = colours
        self.temporary = temporary

    def format_node(self) -> str :
        if len(self.colours) > 1 :
            colour = f"{self.colours[0]};0.5:{self.colours[1]}"
        else :
            colour = self.colours[0]
        return f"{self.graph_id} [label=\"{self.name}\" fillcolor=\"{colour}\"];"

class node_connection:
    def __init__(self, from_id: str, to_id: str, temporary: bool):
        self.from_id = from_id
        self.to_id = to_id
        self.temporary = temporary

    def format_connection(self) -> str :
        res = f"{self.from_id}->{self.to_id}"
        if self.temporary:
            res = f"{res} [style=dashed]"
        return res

class group_subgraph:
    def __init__(self, number: int, name: str):
        self.number = number
        self.name = name
        self.graph_id: str = f"g{self.number:04d}"
        self.sub_nodes: dict[str | None, form_node] = {}
        self.intra_connections: list[node_connection] = []

    def add_sub_node(self, id: str | None, name: str, colours: list[str], temporary: bool) :
        if id is None :
            graph_id = f"f{self.number:04d}"
        else:
            graph_id = f"f{self.number:04d}_{id}".replace('-', '_')
        self.sub_nodes[id] = form_node(graph_id, name, colours, temporary)

    def format_group(self, lines: list[str], prefix: str):
        if len(self.sub_nodes) > 1 :
            lines.append(f"{prefix}    subgraph {self.graph_id} {{")
            lines.append(f"{prefix}        label=\"{self.name}\";")
            lines.append(f"{prefix}        style=\"rounded\";")
            #lines.append(f"{prefix}        style=\"dashed,rounded\"")
            lines.append(f"{prefix}        color=\"#d1d1d1\";")
            lines.append(f"{prefix}        fontcolor=\"#d1d1d1\";")
            lines.append('')
            for sub_node in self.sub_nodes.values() :
                lines.append(f"{prefix}        {sub_node.format_node()}")
            for conn in self.intra_connections :
                lines.append(f"{prefix}        {conn.format_connection()};")
            lines.append(f"{prefix}    }}")
        else:
            sub_node = next(iter(self.sub_nodes.values()))
            lines.append(f"{prefix}    {sub_node.format_node()}")

class evolution_lineage:
    def __init__(self, number: int):
        self.graph_id: str = f"l{number:04d}"
        self.groups: dict[int, group_subgraph] = {}
        self.inter_connections: list[node_connection] = []

    def format_lineage(self, lines: list[str]):
        if len(self.groups) == 1 :
            node: group_subgraph = next(iter(self.groups.values()))
            node.format_group(lines, '')
            lines.append('')
            return
        lines.append(f"    subgraph {self.graph_id} {{")
        lines.append('        style="invis";')
        # lines.append('        style="rounded";')
        # lines.append('        color="#878787";')
        lines.append('')
        for node in self.groups.values() :
            node.format_group(lines, '    ')
            lines.append('')
        if len(self.inter_connections) == 0 :
            lines.pop()
        for conn in self.inter_connections :
            lines.append(f"        {conn.format_connection()};")
        lines.append('    }')
        lines.append('')

class dot_diagram:
    def __init__(self):
        self.pending_forms: deque[tuple[group_subgraph, int]] = deque()
        self.lineages: list[evolution_lineage] = []
        self.group_indexes: dict[int, int] = {}

    def get_lineage(self, group_number: int):
        return self.lineages[self.group_indexes[group_number]]

    def _try_register_form(self, group: group_subgraph, evolved_from: int):
        if not evolved_from in self.group_indexes :
            self.pending_forms.append((group, evolved_from))
            return
        form_index = self.group_indexes[evolved_from]
        self.group_indexes[group.number] = form_index
        self.lineages[form_index].groups[group.number] = group

    def add_group(self, number: int, name: str, evolved_from: int | None) -> group_subgraph :
        node = group_subgraph(number, name)
        if evolved_from is None :
            lineage = evolution_lineage(len(self.lineages) + 1)
            lineage.groups[node.number] = node
            self.lineages.append(lineage)
            self.group_indexes[node.number] = len(self.lineages) - 1
        else:
            self._try_register_form(node, evolved_from)
        return node

    def finish_lineage_processing(self):
        while len(self.pending_forms) > 0 :
            (group, evolved_from) = self.pending_forms.popleft()
            # print(f"Retry {group.name} #{group.number} (from #{evolved_from})")
            self._try_register_form(group, evolved_from)

    def get_lines(self) -> list[str] :
        res: list[str] = [
            'digraph G {',
            '    center=true;',
            '    compound=true;',
            '    splines=polyline;',
            '    fontname="Fira Code";',
            '    rankdir="LR";',
            '',
            '    graph [cluster=true penwidth=2];',
            '',
            # striped ?'
            '    node [shape=rectangle group="g1" style="filled,rounded" color=transparent fontname="Fira Code" fontcolor=white margin=0.2];',
            ''
        ]

        for lineage in self.lineages :
            lineage.format_lineage(res)

        res.append('}')

        return res



def main() -> int :
    pokemon_data = load_groups()

    type_data = load_types()

    diagram = dot_diagram()

    for group in pokemon_data :
        group_name = group.common_names.en if group.common_names is not None else group.forms[0].names.en
        node: group_subgraph = diagram.add_group(group.number, group_name, group.evolves_from)
        for form in group.forms :
            colours: list[str] = [type_data[type_id].colour for type_id in form.types]
            node.add_sub_node(form.variant, form.names.en, colours, form.is_temporary())
    diagram.finish_lineage_processing()

    for group in pokemon_data :
        lineage = diagram.get_lineage(group.number)
        node = lineage.groups[group.number]
        for form in group.forms :
            form_graph_id = node.sub_nodes[form.variant].graph_id
            if form.derives is not None :
                for derivation_variant in form.derives.from_variants :
                    deriv_graph_id = node.sub_nodes[derivation_variant].graph_id
                    node.intra_connections.append(node_connection(deriv_graph_id, form_graph_id, form.is_temporary()))
        if group.evolves_from is not None :
            pre_node = lineage.groups[group.evolves_from]
            for form in group.forms :
                form_graph_id = node.sub_nodes[form.variant].graph_id
                if form.derives is not None :
                    continue
                if form.evolution_variants is not None :
                    for evolution_variants in form.evolution_variants :
                        pre_graph_id = pre_node.sub_nodes[evolution_variants].graph_id
                        lineage.inter_connections.append(node_connection(pre_graph_id, form_graph_id, False))
                elif form.variant is not None and form.variant in pre_node.sub_nodes :
                    pre_graph_id = pre_node.sub_nodes[form.variant].graph_id
                    lineage.inter_connections.append(node_connection(pre_graph_id, form_graph_id, False))
                elif len(pre_node.sub_nodes) > 0 :
                    pre_graph_id = pre_node.sub_nodes[None].graph_id
                    lineage.inter_connections.append(node_connection(pre_graph_id, form_graph_id, False))
                else:
                    lineage.inter_connections.append(node_connection(pre_node.graph_id, form_graph_id, False))

    os.makedirs(dest_dir, exist_ok=True)
    
    with open(os.path.join(dest_dir, 'pokemon.dot'), 'w') as f:
        f.write("\n".join(diagram.get_lines()))

        



if __name__ == '__main__':
    sys.exit(main())
