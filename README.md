# civet_volumetric_atlas
Scripts to map a volumetric atlas to CIVET surfaces.

A common procedure in neuroimaging is to take a volumetric (3D) atlas and map it onto the cortical surface. These scripts help with this procedure when the surfaces come from the CIVET pipeline.

Briefly, the idea is to randomly select a set of processed subjects, align their processed T1-weighted images to the atlas template, transform the processed and resampled ("rsl") mid-surfaces onto the template using the transforms obtained from the previous step, and determine the atlas label at each vertex. A vertex vote is then carried out across all the sampled subjects to determine a singular label at each vertex.

## Requirements

These scripts require:
- minc-toolkit-v2
- ANTs
- VTK
- ITK
- itk-vtkglue

## Align surfaces to the atlas

1. Run `setup_alignment.py`. This sets up the pipeline to be run, and requires the CIVET output directory, template (over which the atlas labels are defined, and registration output directory (where all the outputs of the subsequent steps will be written out). The registration output directory will contain scripts to be run; these can be run with GNU parallel and the number of threads can be customized.
2. Run `registrations.sh` in the registration output directory. This can be run locally, in parallel to speed things up (but note that this might require a fair amount of memory), or passed to a compute cluster. 
3. Run `surface_transforms.sh` when the registrations are complete. This will transform surfaces to the template.

## Get labels at vertices

Once the surfaces are transformed onto the atlas template, run `probe_labels.py` to get label values at each vertex. This script requires one or more surfaces, determines the closest (non-zero) label to each vertex in each surface, and subsequently carries out a vertex vote.  
