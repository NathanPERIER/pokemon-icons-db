
import os
import json

from enum import Enum
from functools import lru_cache

import jsonschema
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


def load_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)


schemas_base_path = 'schemas'
schemas_base_uri = 'schema://pokemon-icons.db/'
@lru_cache(maxsize=20)
def retrieve_schema(uri: str):
    # This is probably obsolete
    if uri.startswith(schemas_base_uri):
        schema_path = uri[len(schemas_base_uri):]
        return Resource.from_contents(load_json(schema_path))
    # This works because we only load schemas in '<root>/schemas/common'
    if uri.startswith('./'):
        filename = os.path.basename(uri)
        schema_path = os.path.join(schemas_base_path, 'common', filename)
        return Resource.from_contents(load_json(schema_path))
    raise NoSuchResource(ref=uri)

registry = Registry(retrieve=retrieve_schema)


def load_validated_json(filename: str):
    data = load_json(filename)
    # TODO: this is not ideal (should fetch only once)
    # but in practice we only load the data once, so it is sufficient
    schema = load_json(os.path.join(schemas_base_path, filename))
    jsonschema.validate(data, schema, registry=registry)
    return data


class pkmn_gender_ratio(Enum):
    MALE_ONLY = "only-m"
    M7_F1 = "7m-1f"
    M3_F1 = "3m-1f"
    M1_F1 = "1m-1f"
    F3_M1 = "3f-1m"
    F7_M1 = "7f-1m"
    FEMALE_ONLY = "only-f"
    UNGENDERED = "ungendered"

    def is_mixed(self) -> bool :
        return self not in [ pkmn_gender_ratio.MALE_ONLY, pkmn_gender_ratio.FEMALE_ONLY, pkmn_gender_ratio.UNGENDERED ]

class pkmn_names:
    def __init__(self, data):
        self.fr: str = data['fr']
        self.en: str = data['en']

class pkmn_links:
    def __init__(self, data):
        self.bulbapedia: str = data['bulbapedia']
        self.pokepedia: str = data['pokepedia']

class pkmn_derivation:
    def __init__(self, data):
        self.from_variants: list[str | None] = data['from']
        self.battle_only: bool = data['battle_only']

class pkmn_form:
    def __init__(self, data):
        self.names = pkmn_names(data['names'])
        self.links = pkmn_links(data['links'])
        self.types: list[str] = data['types']
        self.gen: int = data['gen']
        self.variant: str | None = data['variant'] if 'variant' in data else None
        self.evolution_variants: list[str] | None = data['evolution_variants'] if 'evolution_variants' in data else None
        self.gender_variant: bool = data['gender_variant'] if 'gender_variant' in data else False
        self.gender_ratio = pkmn_gender_ratio(data['gender_ratio']) if 'gender_ratio' in data and data['gender_ratio'] is not None else None
        self.derives: pkmn_derivation | None = None
        if 'derives' in data and data['derives'] is not None :
            self.derives = pkmn_derivation(data['derives'])
    
    def is_temporary(self) -> bool :
        return self.derives is not None and self.derives.battle_only

class pkmn_group:
    def __init__(self, data):
        self.number: int = data['number']
        self.common_names: pkmn_names | None = None
        if 'common_names' in data and data['common_names'] is not None :
            self.common_names = pkmn_names(data['common_names'])
        self.evolves_from: int | None = data['evolves_from']
        self.forms: list[pkmn_form] = list(pkmn_form(x) for x in data['forms'])
    
    def find_form(self, variant: str | None) -> pkmn_form | None :
        return next(filter(lambda x: x.variant == variant, self.forms), None)

class pkmn_type:
    def __init__(self, data):
        self.names = pkmn_names(data['names'])
        self.colour: str = data['colour']
        self.strong_against: list[str] = data['strong_against']
        self.weak_against: list[str] = data['weak_against']
        self.ineffective_against: list[str] = data['ineffective_against']

def load_groups() -> list[pkmn_group] :
    data = load_validated_json('pokemon.json')
    return list(pkmn_group(x) for x in data)

def load_types() -> dict[str, pkmn_type] :
    data = load_validated_json('types.json')
    return { type_id: pkmn_type(type_data) for type_id, type_data in data.items() }
