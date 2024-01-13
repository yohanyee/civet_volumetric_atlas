#!/usr/bin/env python3

import argparse
import os
from random import sample
from shutil import copyfile

parser = argparse.ArgumentParser(description="Registration of a template to CIVET resampled outputs")
parser.add_argument('template', type=str, help='Template (registration target)')
parser.add_argument('civet_outdir', type=str, help='CIVET directory of individual outputs')
parser.add_argument('registration_outdir', type=str, help='Output path')
parser.add_argument('-n', '--num_registrations', type=int, default=None, help='Number of random registrations (default: min(number of civet outputs, 10))')
parser.add_argument('-p', '--parallel', action='store_true', help="Wrap jobs with GNU parallel")
parser.add_argument('-j', '--threads_registration', type=int, default=2, help='Number of GNU parallel threads for registration')
parser.add_argument('-r', '--threads_transform', type=int, default=5, help='Number of GNU parallel threads for object transformations')
args = parser.parse_args()

# %% Get registration inputs

civet_ids = os.listdir(args.civet_outdir)
n_total_outputs = len(civet_ids)
n_registrations = min(n_total_outputs, 10) if args.num_registrations is None else min(n_total_outputs, args.num_registrations)
sampled_ids = sample(civet_ids, n_registrations)

# %% Setup output directory

os.makedirs(args.registration_outdir, exist_ok=False)
os.makedirs(os.path.join(args.registration_outdir, 'registrations'), exist_ok=False)
os.makedirs(os.path.join(args.registration_outdir, 'logs'), exist_ok=False)
for sid in sampled_ids:
    os.makedirs(os.path.join(args.registration_outdir, 'registrations', sid), exist_ok=False)
copyfile(args.template, os.path.join(args.registration_outdir, 'template{ext}'.format(ext=os.path.splitext(args.template)[1])))

# %% Setup commands
# Registrations
registration_cmd_list = []
for sid in sampled_ids:
    log_file = os.path.join(args.registration_outdir, 'logs', 'antsRegistration_{}_to_template.log'.format(sid))
    moving_image = os.path.join(args.civet_outdir, sid, 'final', '{}_t1_final.mnc'.format(sid))
    output_prefix = os.path.join(args.registration_outdir, 'registrations', sid, '{}_to_template'.format(sid))
    cmd = """/usr/bin/time -v antsRegistration \
--minc \
-z 1 \
-d 3 \
-o {o} \
-n Linear \
--initial-moving-transform [{m},{f},1] \
--transform Rigid[0.1] \
--metric MI[{m},{f},1,32,Regular,0.25] \
--convergence [1000x500x250x100,1e-6,10] \
--shrink-factors 8x4x2x1 \
--smoothing-sigmas 3x2x1x0vox \
--transform Affine[0.1] \
--metric MI[{m},{f},1,32,Regular,0.25] \
--convergence [1000x500x250x100,1e-6,10] \
--shrink-factors 8x4x2x1 \
--smoothing-sigmas 3x2x1x0vox \
--transform SyN[0.1,3,0] \
--metric MI[{m},{f},1,32,Regular,0.25] \
--convergence [100x70x50x20,1e-6,10] \
--shrink-factors 8x4x2x1 \
--smoothing-sigmas 3x2x1x0vox \
--use-histogram-matching \
--verbose &> {l}
""".format(m=moving_image, o=output_prefix, f=args.template, l=log_file)
    registration_cmd_list.append(cmd)

# Transform left
transform_cmd_list_left = []
for sid in sampled_ids:
    log_file = os.path.join(args.registration_outdir, 'logs', 'transform_objects_{}_mid_surface_rsl_left_81920.log'.format(sid))
    input_object = os.path.join(args.civet_outdir, sid, 'surfaces', '{}_mid_surface_rsl_left_81920.obj'.format(sid))
    input_transform = os.path.join(args.registration_outdir, 'registrations', sid, '{}_to_template.xfm'.format(sid))
    output_object = os.path.join(args.registration_outdir, 'registrations', sid, '{}_mid_surface_rsl_left_81920_on_template.obj'.format(sid))
    cmd = ("""/usr/bin/time -v transform_objects {i} {x} {o} &> {l}
""").format(i=input_object, x=input_transform, o=output_object, l=log_file)
    transform_cmd_list_left.append(cmd)

# Transform right
transform_cmd_list_right = []
for sid in sampled_ids:
    log_file = os.path.join(args.registration_outdir, 'logs', 'transform_objects_{}_mid_surface_rsl_right_81920.log'.format(sid))
    input_object = os.path.join(args.civet_outdir, sid, 'surfaces', '{}_mid_surface_rsl_right_81920.obj'.format(sid))
    input_transform = os.path.join(args.registration_outdir, 'registrations', sid, '{}_to_template.xfm'.format(sid))
    output_object = os.path.join(args.registration_outdir, 'registrations', sid, '{}_mid_surface_rsl_right_81920_on_template.obj'.format(sid))
    cmd = """/usr/bin/time -v transform_objects {i} {x} {o} &> {l}
""".format(i=input_object, x=input_transform, o=output_object, l=log_file)
    transform_cmd_list_left.append(cmd)

# %% Write commands
# Write registration command file
with open(os.path.join(args.registration_outdir, 'registrations.sh'), "w") as fconn:
    fconn.writelines('#!/bin/bash\n')
    if args.parallel:
        fconn.writelines('parallel -j {} << EOF\n'.format(args.threads_registration))
    fconn.writelines(registration_cmd_list)
    if args.parallel:
        fconn.writelines('EOF\n')

# Write transforms command file
with open(os.path.join(args.registration_outdir, 'surface_transforms.sh'), "w") as fconn:
    fconn.writelines('#!/bin/bash\n')
    if args.parallel:
        fconn.writelines('parallel -j {} << EOF\n'.format(args.threads_transform))
    fconn.writelines(transform_cmd_list_left)
    fconn.writelines(transform_cmd_list_right)
    if args.parallel:
        fconn.writelines('EOF\n')

# Write IDs
with open(os.path.join(args.registration_outdir, 'civet_ids.txt'), "w") as fconn:
    for sid in sampled_ids:
        fconn.writelines('{}\n'.format(sid))
