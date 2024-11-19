import copy
import pprint

import rmsapi  # type: ignore
import rmsapi.jobs  # type: ignore
import yaml

# User defined global variables
DEBUG_PRINT = False
REPORT_UNUSED = True
CONFIG_FILE = "generate_petro_jobs.yml"

# Fixed global variables
GRID_MODELS = "Grid models"
GRID = "Grid"
JOB_TYPE = "Petrophysical Modeling"
PP = pprint.PrettyPrinter(depth=7)


def main():
    spec_dict = read_specification_file(CONFIG_FILE)
    create_new_petro_job_per_facies(spec_dict)


def read_specification_file(config_file_name):
    with open(config_file_name, encoding="utf-8") as yml_file:
        return yaml.safe_load(yml_file)


def define_new_variable_names_and_correlation_matrix(
    orig_var_names, var_names_to_keep, facies_name, orig_corr_matrix
):
    nvar_new = len(var_names_to_keep)
    if nvar_new == 1:
        # No correlation matrix
        new_variable_names = []
        new_variable_names.append(facies_name + "_" + var_names_to_keep[0])
        return new_variable_names, []

    # Order the var_names_to_keep list to be in same sequence
    # as orig_var_names for those variables that are common with the var_names_to_keep
    # Example: the keep list is: ["A", "C",  "B"]
    # and the original var name list
    # is ["A", "D", "F", "B", "C"]
    # The sorted keep list should be: ["A", "B", "C"]

    sorted_keep_list = sort_new_var_names(orig_var_names, var_names_to_keep)
    new_corr_matrix = []
    index_in_orig_var = []
    for i, var_name in enumerate(orig_var_names):
        if var_name in sorted_keep_list:
            index_in_orig_var.append(i)

    for row in range(nvar_new):
        row_list = []
        for col in range(row):
            row_list.append(
                orig_corr_matrix[index_in_orig_var[row]][index_in_orig_var[col]]
            )
        new_corr_matrix.append(row_list)

    new_variable_names = []
    # Here it is important to use the sorted version of the keep list
    # to get correct variables connected to each row and column in
    # the new correlation matrix
    for var_name in sorted_keep_list:
        new_variable_names.append(facies_name + "_" + var_name)
    return new_variable_names, new_corr_matrix


def sort_new_var_names(original_variable_names, variable_names_to_keep):
    sorted_keep_list = []
    for varname in original_variable_names:
        if varname in variable_names_to_keep:
            sorted_keep_list.append(varname)
    return sorted_keep_list


def get_original_job_settings(owner_string_list, job_type, job_name):
    original_job = rmsapi.jobs.Job.get_job(owner_string_list, job_type, job_name)
    return original_job.get_arguments(skip_defaults=False)


def create_copy_of_job(
    owner_string_list, job_type, original_job_arguments, new_job_name
):
    new_job = rmsapi.jobs.Job.create(owner_string_list, job_type, new_job_name)
    new_job.set_arguments(original_job_arguments)
    return new_job


def get_zone_names_per_facies(used_petro_per_zone_per_facies_dict):
    zone_names_with_facies_dict = {}
    for zone_name, facies_dict in used_petro_per_zone_per_facies_dict.items():
        for facies_name, _ in facies_dict.items():
            if facies_name not in zone_names_with_facies_dict:
                zone_names_with_facies_dict[facies_name] = []
            zone_names_with_facies_dict[facies_name].append(zone_name)
    return zone_names_with_facies_dict


def get_used_petro_names(used_petro_per_zone_per_facies_dict):
    all_petro_var_list = []
    for _, petro_per_facies_dict in used_petro_per_zone_per_facies_dict.items():
        for _, petro_list in petro_per_facies_dict.items():
            for petro_name in petro_list:
                if petro_name not in all_petro_var_list:
                    all_petro_var_list.append(petro_name)
    return all_petro_var_list


def check_consistency(
    owner_string_list, job_name, used_petro_per_zone_per_facies_dict, report_unused=True
):
    job_arguments = get_original_job_settings(owner_string_list, JOB_TYPE, job_name)
    zone_models_list = job_arguments["Zone Models"]

    if report_unused:
        # First report which field parameters from original model
        # that is not specified to be used
        print("Report of unused petrophysical variables in generated jobs:")
        for zone_model in zone_models_list:
            zone_name = zone_model["ZoneName"]
            if zone_name not in used_petro_per_zone_per_facies_dict:
                print(f" No field parameters are used from zone: {zone_name}")
            else:
                petro_per_facies_dict = used_petro_per_zone_per_facies_dict[zone_name]
                facies_models_list = zone_model["Facies Models"]
                for facies_model in facies_models_list:
                    facies_name = facies_model["FaciesName"]
                    petro_model_list = facies_model["Variable Models"]
                    if facies_name not in petro_per_facies_dict:
                        print(
                            " No field parameters are used for facies "
                            f"{facies_name} for zone {zone_name}"
                        )
                    else:
                        petro_list = petro_per_facies_dict[facies_name]
                        for petro_model in petro_model_list:
                            var_name = petro_model["VariableName"]
                            if var_name not in petro_list:
                                print(
                                    f" Field parameter {var_name} is not used "
                                    f"for facies {facies_name} for zone {zone_name}"
                                )
        print("")

    # Check if there are specified field parameters which does not exist
    # in the original job and report errors if this is the case
    specified_petro_var_list = get_used_petro_names(used_petro_per_zone_per_facies_dict)
    err_list = []
    for specified_petro_var in specified_petro_var_list:
        found = False
        for zone_model in zone_models_list:
            facies_models_list = zone_model["Facies Models"]
            for facies_model in facies_models_list:
                petro_model_list = facies_model["Variable Models"]
                for petro_model in petro_model_list:
                    if specified_petro_var == petro_model["VariableName"]:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            err_list.append(specified_petro_var)
    if len(err_list) > 0:
        print("Error in specification of used petrophysical variables.")
        print("Unknown petrophysical variables:")
        for name in err_list:
            print(f"{name}")
        raise ValueError("Unknown petrophysical variable names are specified.")


def create_new_petro_job_per_facies(spec_dict):
    debug_print = DEBUG_PRINT
    grid_name = spec_dict["grid_name"]
    original_job_name = spec_dict["original_job_name"]
    used_petro_per_zone_per_facies_dict = spec_dict["used_petro_var"]

    # Original job parameter setting
    owner_string_list = [GRID_MODELS, grid_name, GRID]
    check_consistency(
        owner_string_list,
        original_job_name,
        used_petro_per_zone_per_facies_dict,
        report_unused=REPORT_UNUSED,
    )
    orig_job_arguments = get_original_job_settings(
        owner_string_list, JOB_TYPE, original_job_name
    )

    zone_names_per_facies_dict = get_zone_names_per_facies(
        used_petro_per_zone_per_facies_dict
    )

    # for each facies used in any zone, find the zone models having the facies
    original_zone_models_list = orig_job_arguments["Zone Models"]
    new_job_name_list = []
    for facies_name, zone_name_list in zone_names_per_facies_dict.items():
        if debug_print:
            print(f"Facies:  {facies_name}")
        new_job_arguments_current = copy.deepcopy(orig_job_arguments)
        # Remove unused keys or keys that should be set to default for new job
        del new_job_arguments_current["InputFaciesProperty"]
        del new_job_arguments_current["PrefixOutputName"]

        # Only keep specification for zones having the facies
        new_job_arguments_current["Zone Models"] = []
        for zone_model_dict in original_zone_models_list:
            zone_name = zone_model_dict["ZoneName"]
            if zone_name in zone_name_list:
                zone_model_dict_current = copy.deepcopy(zone_model_dict)
                new_job_arguments_current["Zone Models"].append(zone_model_dict_current)
                # for this zone model remove all specifications not relevant
                # for current facies_name

                used_petro_var_list = used_petro_per_zone_per_facies_dict[zone_name][
                    facies_name
                ]

                tmp_list = zone_model_dict_current["Facies Models"]
                # Loop over facies for this zone and keep only current facies
                new_facies_model_list = []
                for facies_model_dict in tmp_list:
                    if facies_model_dict["FaciesName"] == facies_name:
                        new_facies_model_list.append(facies_model_dict)
                        break
                # Here at least one facies model must exist in the list if
                # not there is a consistency error in input dictionary
                # used_petro_per_zone_per_facies_dict related to the
                # specified original job.
                if len(new_facies_model_list) == 0:
                    raise ValueError(
                        "There are some facies name errors in input dict"
                        " 'used_petro_per_zone_per_facies_dict'. "
                        "Check consistency with original job "
                        f"'{original_job_name}' and facies name '{facies_name}'"
                    )
                zone_model_dict_current["Facies Models"] = new_facies_model_list
                # Use new property names consisting of facies_name + petro_name
                original_variable_names = orig_job_arguments["VariableNames"]

                corr_model = zone_model_dict_current["Facies Models"][0]
                original_corr_model_dict = corr_model["Correlation Model"][
                    0
                ]  # Only one element in this always ??????????
                original_corr_matrix = original_corr_model_dict["CorrelationMatrix"]
                new_variable_names, new_corr_matrix = (
                    define_new_variable_names_and_correlation_matrix(
                        original_variable_names,
                        used_petro_var_list,
                        facies_name,
                        original_corr_matrix,
                    )
                )

                original_corr_model_dict["CorrelationMatrix"] = new_corr_matrix
                new_job_arguments_current["VariableNames"] = new_variable_names

                # Replace old petro names with new petro names
                variable_models_list = corr_model["Variable Models"]
                variable_models_list_to_keep = []
                for indx, variable_model in enumerate(variable_models_list):
                    var_name = variable_model["VariableName"]
                    new_var_name = facies_name + "_" + var_name
                    if new_var_name in new_variable_names:
                        variable_model["VariableName"] = new_var_name
                        variable_models_list_to_keep.append(variable_model)
                corr_model["Variable Models"] = variable_models_list_to_keep

        new_job_name = facies_name + "_petro"
        new_job_name = new_job_name.lower()
        new_job_name_list.append(new_job_name)
        print(f"Create job:  {new_job_name}")
        if debug_print:
            PP.pprint(new_job_arguments_current)
            print("-" * 100)
        new_job = create_copy_of_job(
            owner_string_list, JOB_TYPE, new_job_arguments_current, new_job_name
        )
        ok, err_msg_list, warn_msg_list = rmsapi.jobs.Job.check(new_job)
        if not ok:
            print("Error messages from created job object:")
            for err_msg in err_msg_list:
                print(f"{err_msg}")
            print("\n")
            print("Warnings from created job object:")
            for warn_msg in warn_msg_list:
                print(f"{warn_msg}")
            print(f"\nThe job with name  {new_job_name} is not saved.")
        else:
            print(f"Save new job: {new_job_name}")
            new_job.save()
    return new_job_name_list


def write_petro_job_to_file(owner_string_list, job_type, job_name):
    job_instance = rmsapi.jobs.Job.get_job(
        owner=owner_string_list, type=job_type, name=job_name
    )
    arguments = job_instance.get_arguments(True)
    filename = job_name + ".txt"
    print(f"Write file: {filename}")
    with open(filename, "w") as outfile:
        pprint.pp(arguments, depth=15, width=150, indent=3, stream=outfile)
        outfile.write("_" * 150)
        outfile.write("\n")


if __name__ == "__main__":
    main()
