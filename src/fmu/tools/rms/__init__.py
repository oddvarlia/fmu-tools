"""
Processing of volumetrics from RMS
"""

from .generate_petro_jobs_for_field_update import (
    main as generate_petro_jobs,
)
from .import_localmodules import import_localmodule
from .update_petro_real_from_fields_per_facies import (
    main as update_petro_real,
)
from .volumetrics import rmsvolumetrics_txt2df

__all__ = [
    "rmsvolumetrics_txt2df",
    "import_localmodule",
    "generate_petro_jobs",
    "update_petro_real",
]
