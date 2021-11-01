# pylint:disable=unused-argument
""" Defines various validation functions that get used to ensure inputs are legit """

import pydantic

from ..log import ValidationError, SetupError
from .geometry import Box


def assert_plane():
    """makes sure a field's `size` attribute has exactly 1 zero"""

    @pydantic.validator("size", allow_reuse=True, always=True)
    def is_plane(cls, val):
        if val.count(0.0) != 1:
            raise ValidationError(f"'{cls.__name__}' object must be planar, given size={val}")
        return val

    return is_plane


def validate_name_str():
    """make sure the name doesnt include [, ] (used for default names)"""

    @pydantic.validator("name", allow_reuse=True, always=True, pre=True)
    def field_has_unique_names(cls, val):
        """raise exception if '[' or ']' in name"""
        # if val and ('[' in val or ']' in val):
        #     raise SetupError(f"'[' or ']' not allowed in name: {val} (used for defaults)")
        return val

    return field_has_unique_names


def assert_unique_names(field_name: str, check_mediums=False):
    """makes sure all elements of a field have unique .name values"""

    @pydantic.validator(field_name, allow_reuse=True, always=True)
    def field_has_unique_names(cls, val, values):
        """check for intersection of each structure with simulation bounds."""
        if check_mediums:
            background = values.get("medium")
            field_names = [background] + [field.medium.name for field in val if field.medium.name]
            field_names = [name for name in field_names if ("]" not in name) or ("[" not in name)]
        else:
            field_names = [field.name for field in val if field.name]
        unique_names = set(field_names)
        if len(unique_names) != len(field_names):
            raise SetupError(f"'{field_name}' names are not unique, given {field_names}.")
        return val

    return field_has_unique_names


def assert_objects_in_sim_bounds(field_name: str):
    """makes sure all objects in field are at least partially inside of simulation bounds/"""

    @pydantic.validator(field_name, allow_reuse=True, always=True)
    def objects_in_sim_bounds(cls, val, values):
        """check for intersection of each structure with simulation bounds."""
        sim_bounds = Box(size=values.get("size"), center=values.get("center"))
        for position_index, geometric_object in enumerate(val):
            if not sim_bounds.intersects(geometric_object.geometry):
                raise SetupError(
                    f"'{geometric_object}' "
                    f"(at `simulation.{field_name}[{position_index}]`)"
                    "is completely outside of simulation domain"
                )
        return val

    return objects_in_sim_bounds


def set_names(field_name: str):
    """set names"""

    @pydantic.validator(field_name, allow_reuse=True, always=True)
    def set_unique_names(cls, val):
        """check for intersection of each structure with simulation bounds."""
        for position_index, geometric_object in enumerate(val):
            if not geometric_object.name:
                geometric_object.name = f"{field_name}[{position_index}]"
        return val

    return set_unique_names
