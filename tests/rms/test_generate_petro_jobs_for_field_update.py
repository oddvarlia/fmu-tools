import pprint

from generate_petro_jobs_for_field_update import (
    create_new_petro_job_per_facies,
    define_new_variable_names_and_correlation_matrix,
    get_original_job_settings,
)

PP = pprint.PrettyPrinter(depth=7)


def test_define_new_variable_names_and_correlation_matrix():
    original_variable_names = ["phit", "vsh", "klogh", "vphyl"]
    variable_names_to_keep = ["klogh", "phit"]
    facies_name = "Floodplain"
    original_Lcorr_mat = [[], [0.2], [0.3, 0.4], [0.5, 0.6, 0.7]]

    new_variable_names, new_Lcorr_mat = (
        define_new_variable_names_and_correlation_matrix(
            original_variable_names,
            variable_names_to_keep,
            facies_name,
            original_Lcorr_mat,
        )
    )

    print(f"Original var names:  {original_variable_names}")
    print(f"New var names:       {new_variable_names}")
    print(f"Original correlations:  {original_Lcorr_mat}")
    print(f"New correlations:       {new_Lcorr_mat}")


def test_get_original_job_with_settings(grid_name, job_name):
    owner_string_list = ["Grid models", grid_name, "Grid"]
    job_type = "Petrophysical Modeling"
    original_job_arguments = get_original_job_settings(
        owner_string_list, job_type, job_name
    )
    print("Original job arguments:")
    PP.pprint(original_job_arguments)


if __name__ == "__main__":
    test = 2
    #    test_define_new_variable_names_and_correlation_matrix()
    #    test_get_original_job_with_settings("MultiZoneGrid","petro")
    #    print("-"*80)
    #    test_get_original_job_with_settings("SingleZoneGrid","std_valysar")
    #    print("-"*80)
    #    test_get_original_job_with_settings("MultiZoneGrid", "petro_floodplain")
    #    print("-"*80)
    #    test_get_original_job_with_settings("SingleZoneGrid","std_valysar_floodplain")
    #    print("-"*80)
    if test == 1:
        grid_name = "SingleZoneGrid"
        zone_name = "valysar"
        original_job_name = "std_valysar"
        used_petro_per_zone_per_facies_dict = {
            "": {
                "Floodplain": ["PHIT", "KLOGH"],
                "Channel": ["PHIT", "KLOGH"],
                "Crevasse": ["PHIT", "KLOGH"],
            },
        }
    elif test == 2:
        grid_name = "MultiZoneGrid"
        zone_name = None
        original_job_name = "original"
        used_petro_per_zone_per_facies_dict = {
            "Valysar": {
                "Floodplain": ["phit", "klogh"],
                "Channel": ["klogh", "phit"],
                "Crevasse": ["phit", "klogh"],
            },
            "Therys": {
                "Offshore": ["phit", "klogh"],
                "Lowershoreface": ["phit", "klogh"],
                "Uppershoreface": ["phit", "klogh"],
                "Calcite": ["phit"],
            },
            "Volon": {
                "Floodplain": ["phit", "klogh"],
                "Channel": ["phit", "klogh"],
                "Calcite": ["phit"],
            },
        }

    create_new_petro_job_per_facies(
        grid_name, original_job_name, used_petro_per_zone_per_facies_dict, zone_name
    )
