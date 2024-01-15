#!/usr/bin/env python3

import argparse
from itk import imread
from itk import vtk_image_from_image
from vtkmodules.all import vtkMNIObjectReader
from vtkmodules.all import vtkPointLocator
from vtkmodules.all import vtkPoints, vtkPolyData
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Probe label values at each vertex of a series of meshes.')
parser.add_argument('label_file', type=str, help='Label volume')
parser.add_argument('output_file', type=str, help='Voted labels')
parser.add_argument('-m', '--mesh', nargs='+', type=str, help='Mesh file(s) aligned to label volume')
parser.add_argument('-p', '--proportion_file', type=str, help='Proportion of votes')
args = parser.parse_args()

# Load input label volume
img_itk = imread(args.label_file)
img = vtk_image_from_image(img_itk)

# Convert image to polydata, dropping non-zero labels
labels = []
points = vtkPoints()
for pt in tqdm(range(img.GetNumberOfPoints()), desc='Processing'):
    point = img.GetPoint(pt)
    l = int(round(img.GetPointData().GetScalars().GetTuple(pt)[0]))
    if l > 0:
        points.InsertNextPoint(img.GetPoint(pt))
        labels.append(l)
poly = vtkPolyData()
poly.SetPoints(points)

img.GetNumberOfPoints()
points.GetNumberOfPoints()
assert points.GetNumberOfPoints() == len(labels)

# Get point labels
all_labels = []
PointLocator = vtkPointLocator()
PointLocator.SetDataSet(poly)
for f in args.mesh:
    # Load mesh
    MeshReader = vtkMNIObjectReader()
    MeshReader.SetFileName(f)
    MeshReader.Update()
    mesh = MeshReader.GetOutputDataObject(0)

    # Get point data at closest point
    mesh_labels = []

    for pt in tqdm(range(mesh.GetNumberOfPoints()), desc=f"Getting vertex labels for file: {f}"):
        img_voxel = PointLocator.FindClosestPoint(mesh.GetPoint(pt))
        img_label = labels[img_voxel]
        mesh_labels.append(img_label)
    all_labels.append(mesh_labels)

# Compute mode and proportion
num_meshes = len(args.mesh)
voted_labels = []
prop_labels = []
for i in tqdm(range(mesh.GetNumberOfPoints()), desc="Vertex vote"):
    vertex_labels = [all_labels[m][i] for m in range(num_meshes)]
    voted_label = max(vertex_labels, key=vertex_labels.count)
    prop_label = sum([ v == voted_label for v in vertex_labels ])/len(vertex_labels)
    voted_labels.append(voted_label)
    prop_labels.append(prop_label)

# Write out data
with open(args.output_file, "w") as fconn:
    fconn.write('\n'.join([str(l) for l in voted_labels]))

if args.proportion_file is not None:
    with open(args.proportion_file, "w") as fconn:
        fconn.write('\n'.join([str(l) for l in prop_labels]))