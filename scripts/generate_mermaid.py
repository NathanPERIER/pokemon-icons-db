
import os
import sys

from pokemon_data import load_groups


dest_dir = 'diagrams'


class state_sub_node:
    def __init__(self, graph_id: str, name: str, temporary: bool):
        self.graph_id = graph_id
        self.name = name
        self.temporary = temporary

class state_node:
    def __init__(self, number: int, name: str):
        self.number = number
        self.name = name
        self.sub_nodes: dict[str | None, state_sub_node] = {}
        self.intra_connections: list[tuple[str, str]] = []

    def add_sub_node(self, id: str | None, name: str, temporary: bool) :
        if id is None :
            graph_id = f"f{self.number:04d}"
        else:
            graph_id = f"f{self.number:04d}_{id}".replace('-', '_')
        self.sub_nodes[id] = state_sub_node(graph_id, name, temporary)
    
    def graph_id(self) -> str :
        return f"g{self.number:04d}"

class state_diagram:
    def __init__(self):
        self.nodes: dict[int, state_node] = {}
        self.inter_connections: list[tuple[str, str]] = []
    
    def get_lines(self) -> list[str] :
        res: list[str] = [
            'stateDiagram-v2',
            '    direction TB',
            '    classDef temporary font-style:italic',
            ''
        ]

        for node in self.nodes.values() :
            graph_id = node.graph_id()
            res.append(f"    state \"{node.name}\" as {graph_id}")
            if len(node.sub_nodes) > 0 :
                res[-1] += " {"
                for sub_node in node.sub_nodes.values() :
                    res.append(f"        state \"{sub_node.name}\" as {sub_node.graph_id}")
                    if sub_node.temporary :
                        res.append(f"        class {sub_node.graph_id} temporary")
                for conn in node.intra_connections :
                    res.append(f"        {conn[0]} --> {conn[1]}")
                res.append("    }")
            res.append('')

        for conn in self.inter_connections :
            res.append(f"    {conn[0]} --> {conn[1]}")

        return res



def main() -> int :
    pokemon_data = load_groups()
    
    diagram = state_diagram()

    for group in pokemon_data :
        group_name = group.common_names.en if group.common_names is not None else group.forms[0].names.en
        node = state_node(group.number, group_name)
        diagram.nodes[node.number] = node
        if len(group.forms) >= 2 :
            for form in group.forms :
                node.add_sub_node(form.variant, form.names.en, form.is_temporary())
        
    for group in pokemon_data :
        node = diagram.nodes[group.number]
        if group.evolves_from is not None :
            pre_node = diagram.nodes[group.evolves_from]
            for form in group.forms :
                if len(node.sub_nodes) == 0 :
                    form_graph_id = node.graph_id()
                else:
                    form_graph_id = node.sub_nodes[form.variant].graph_id
                if form.evolution_variants is not None :
                    for evolution_variants in form.evolution_variants :
                        pre_graph_id = pre_node.sub_nodes[evolution_variants].graph_id
                        diagram.inter_connections.append((pre_graph_id, form_graph_id))
                elif form.variant is not None and form.variant in pre_node.sub_nodes :
                    pre_graph_id = pre_node.sub_nodes[form.variant].graph_id
                    diagram.inter_connections.append((pre_graph_id, form_graph_id))
                elif len(pre_node.sub_nodes) > 0 :
                    pre_graph_id = pre_node.sub_nodes[None].graph_id
                    diagram.inter_connections.append((pre_graph_id, form_graph_id))
                else:
                    diagram.inter_connections.append((pre_node.graph_id(), form_graph_id))
                if form.derives is not None :
                    for derivation_variant in form.derives.from_variants :
                        deriv_graph_id = node.sub_nodes[derivation_variant].graph_id
                        node.intra_connections.append((deriv_graph_id, form_graph_id))

    try:
        os.mkdir(dest_dir)
    except FileExistsError:
        pass
    
    with open(os.path.join(dest_dir, 'full.mermaid'), 'w') as f:
        f.write("\n".join(diagram.get_lines()))

        



if __name__ == '__main__':
    sys.exit(main())
