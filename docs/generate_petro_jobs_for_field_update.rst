rms.generate_petro_jobs_for_field_update
=========================================

When running FMU project where field parameters for both facies and
petrophysical properties is updated in ERT simultaneously,
some adjustments are needed in the RMS project to support this type
of workflow. It is necessary to have one petrosim job per facies.
To simplify the work with the RMS project,
the script *generate_petro_jobs_for_field_update* can be imported into
RMS as a python job. It requires a small configuration file and will then
read an existing petrosim job from the RMS project and generate one new
petrosim job per facies. The new jobs are ready to be used
(put into the RMS workflow) and they will use the same model parameters
for the petrophysical properties as the original (existing) job,
but only for one facies.

This script will modify your RMS project when run from your RMS project
by adding new petrosim jobs, one per facies as specified in the
configuration file for the script. The configuration file is a yaml format
file defining which grid model and which facies 3D parameter to use and the
name of the original petrosim job. For each zone and each facies per zone
a list is specified of which petrophysical parameters to use in the new
petrosim jobs that are generated.


Usage
^^^^^
Load the script *generate_petro_jobs_for_field_update* into a python job.
Specify a configuration file and specify the name of this configuration file in the
python job for the global variable **CONFIG_FILE**

Run the python job in RMS to generate the new petrosim jobs and
finally update the workflowin RMS by using the generated jobs.
