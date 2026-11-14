
import os
import sys

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

class dot_diagram:
    def __init__(self):
        self.nodes: dict[int, group_subgraph] = {}
        self.inter_connections: list[node_connection] = []
    
    def get_lines(self) -> list[str] :
        res: list[str] = [
            'digraph G {',
            '    center=true;',
            '    compound=true;',
            '    fontname="Fira Code";',
            '    rankdir="LR";',
            '',
            '    graph [cluster=true color="#D1D1D1" style=rounded fontcolor="#D1D1D1" penwidth=2];',
            '',
            # striped ?'
            '    node [shape=rectangle group="g1" style="filled,rounded" color=transparent fontname="Fira Code" fontcolor=white margin=0.2];',
            ''
        ]

        for node in self.nodes.values() :
            if len(node.sub_nodes) > 1 :
                res.append(f"    subgraph {node.graph_id} {{")
                res.append(f"        label=\"{node.name}\"")
                for sub_node in node.sub_nodes.values() :
                    res.append(f"        {sub_node.format_node()}")
                for conn in node.intra_connections :
                    res.append(f"        {conn.format_connection()};")
                res.append('    }')
            else:
                sub_node = next(iter(node.sub_nodes.values()))
                res.append(f"    {sub_node.format_node()}")
            res.append('')

        for conn in self.inter_connections :
            res.append(f"    {conn.format_connection()};")

        res.append('}')

        return res



def main() -> int :
    pokemon_data = load_groups()

    type_data = load_types()

    diagram = dot_diagram()

    for group in pokemon_data :
        group_name = group.common_names.en if group.common_names is not None else group.forms[0].names.en
        node = group_subgraph(group.number, group_name)
        diagram.nodes[node.number] = node
        for form in group.forms :
            colours: list[str] = [type_data[type_id].colour for type_id in form.types]
            node.add_sub_node(form.variant, form.names.en, colours, form.is_temporary())

    for group in pokemon_data :
        node = diagram.nodes[group.number]
        for form in group.forms :
            form_graph_id = node.sub_nodes[form.variant].graph_id
            if form.derives is not None :
                for derivation_variant in form.derives.from_variants :
                    deriv_graph_id = node.sub_nodes[derivation_variant].graph_id
                    node.intra_connections.append(node_connection(deriv_graph_id, form_graph_id, form.is_temporary()))
        if group.evolves_from is not None :
            pre_node = diagram.nodes[group.evolves_from]
            for form in group.forms :
                # if len(node.sub_nodes) == 0 :
                #     form_graph_id = node.graph_id
                # else:
                #     form_graph_id = node.sub_nodes[form.variant].graph_id
                form_graph_id = node.sub_nodes[form.variant].graph_id
                if form.derives is not None :
                    continue
                if form.evolution_variants is not None :
                    for evolution_variants in form.evolution_variants :
                        pre_graph_id = pre_node.sub_nodes[evolution_variants].graph_id
                        diagram.inter_connections.append(node_connection(pre_graph_id, form_graph_id, False))
                elif form.variant is not None and form.variant in pre_node.sub_nodes :
                    pre_graph_id = pre_node.sub_nodes[form.variant].graph_id
                    diagram.inter_connections.append(node_connection(pre_graph_id, form_graph_id, False))
                elif len(pre_node.sub_nodes) > 0 :
                    pre_graph_id = pre_node.sub_nodes[None].graph_id
                    diagram.inter_connections.append(node_connection(pre_graph_id, form_graph_id, False))
                else:
                    diagram.inter_connections.append(node_connection(pre_node.graph_id, form_graph_id, False))

    os.makedirs(dest_dir, exist_ok=True)
    
    with open(os.path.join(dest_dir, 'pokemon.dot'), 'w') as f:
        f.write("\n".join(diagram.get_lines()))

        



if __name__ == '__main__':
    sys.exit(main())
