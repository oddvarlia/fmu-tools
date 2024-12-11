"""
Merge petrophysical realizations created individually per facies
into one realization using facies realization as filter
"""

from typing import Dict, List

import xtgeo

from fmu.tools.rms.generate_petro_jobs_for_field_update import (
    get_original_job_settings,
    read_specification_file,
)

DEBUG_PRINT = True


def main(
    project,
    config_file: str,
    facies_code_names: Dict[int, str],
    zone_code_names: Dict[int, str] = {},
    zone_param_name: str = "",
    debug_print: bool = False,
) -> None:
    """Combine multiple petrophysical realizations (one per facies) into one parameter
    using facies realization as filter.

    Description

        This function will read petrophysical realization for multiple facies
        (where all grid cells have the same facies) and use the facies
        realization to combine them into one realization conditioned to facies.

    Input

        A configuration file in YAML format, a file which is shared also with another
        script that can created the RMS petrophysical jobs to simulate the petrophysical
        realization for each facies individually)
        Grid model name,
        facies realization name,
        optionally zone realization name,
        optionally a dictionary defining for each zone and
        each facies per zone which petrophysical properties are available.
        A dictionary with specification of which facies code and facies names belongs
        to each other and optionally also the same type of dictionary for
        zone code and zone name.

    Output

        Updated version of petrophysical realizations
        for the specified petrophysical variables.

    """
    spec_dict = read_specification_file(config_file)

    used_petro_dict = spec_dict["used_petro_var"]
    grid_name = spec_dict["grid_name"]
    original_job_name = spec_dict["original_job_name"]

    # Get facies param name from the job settings
    owner_string_list = ["Grid models", grid_name, "Grid"]
    job_type = "Petrophysical Modeling"
    petro_job_param = get_original_job_settings(
        owner_string_list, job_type, original_job_name
    )
    facies_real_name = petro_job_param["InputFaciesProperty"]

    update_petro_real(
        project,
        grid_name,
        facies_real_name,
        used_petro_dict,
        facies_code_names,
        zone_param_name=zone_param_name,
        zone_code_names=zone_code_names,
        debug_print=debug_print,
    )


def update_petro_real(
    project,
    grid_name: str,
    facies_real_name: str,
    used_petro_dict: Dict[str, Dict[str, List[str]]],
    facies_code_names: Dict[int, str],
    zone_param_name: str = "",
    zone_code_names: Dict[int, str] = {},
    debug_print: bool = False,
) -> None:
    # Find all petro var names to use in any zone
    petro_var_list = get_petro_var(used_petro_dict)

    # Get facies realization
    prop_facies = xtgeo.gridproperty_from_roxar(project, grid_name, facies_real_name)
    prop_facies_values = prop_facies.values

    # Get zone realization
    if zone_param_name:
        prop_zone = xtgeo.gridproperty_from_roxar(project, grid_name, zone_param_name)
        prop_zone_values = prop_zone.values

    for zone_name, petro_per_facies_dict in used_petro_dict.items():
        if zone_code_names:
            zone_code = code_per_name(zone_code_names, zone_name)
        for pname in petro_var_list:
            prop_petro_original = xtgeo.gridproperty_from_roxar(
                project, grid_name, pname
            )
            prop_petro_original_values = prop_petro_original.values

            for fname in petro_per_facies_dict:
                petro_name_per_facies = f"{fname}_{pname}"

                # Get petro realization for this facies and this petro variable
                prop_petro = xtgeo.gridproperty_from_roxar(
                    project, grid_name, petro_name_per_facies
                )
                prop_petro_values = prop_petro.values

                facies_code = code_per_name(facies_code_names, fname)

                if zone_code_names:
                    if debug_print:
                        print(
                            f"Update values for {pname} "
                            f"in existing parameter for facies {fname} "
                            f"for zone {zone_name}"
                        )
                    cells_selected = (
                        prop_facies_values
                        == facies_code & prop_zone_values
                        == zone_code
                    )
                else:
                    if debug_print:
                        print(
                            f"Update values for {pname} "
                            f"in existing parameter for facies {fname}"
                        )
                    cells_selected = prop_facies_values == facies_code

                prop_petro_original_values[cells_selected] = prop_petro_values[
                    cells_selected
                ]
            prop_petro_original.values = prop_petro_original_values
            if zone_code_names:
                print(
                    f"Write updated petro param {pname} "
                    f"for zone {zone_name} to grid model {grid_name}"
                )
            else:
                print(f"Write updated petro param {pname} to grid model {grid_name}")
            prop_petro_original.to_roxar(project, grid_name, pname)


def code_per_name(code_name_dict: Dict[int, str], input_name: str) -> int:
    # Since name is (must be) unique, get it if found or return -1 if not found
    for code, name in code_name_dict.items():
        if input_name == name:
            return code
    return -1


def get_petro_var(used_petro_dict: Dict[str, Dict[str, List[str]]]) -> List[str]:
    petro_var_list = []
    for _, petro_var_per_facies_dict in used_petro_dict.items():
        for _, petro_list in petro_var_per_facies_dict.items():
            for petro_name in petro_list:
                if petro_name not in petro_var_list:
                    petro_var_list.append(petro_name)
    return petro_var_list
