import os
import batchtools_utilities as batchtools
import subprocess
import demos
from sys import platform

__copyright__ = '@copyright Allegorithmic. All rights reserved.'
__author__ = 'gaetan.lassagne@allegorithmic.com'
VERSION = 'BatchTools demo scripts 0.1'

"""
Module **demos_texturing_template** provides an usage example of the Substance Batchtools "sbsmutator" module
The idea is to have a "texturing automation" system based on meshes baked maps and a sbs template
"""


"""
INITIALIZATION
"""


if __name__ == "__main__":
    batchtools_path = os.path.normpath(demos.get_batchtools_path())

    # Todo: instead of setting paths, assume we can walk ../../current dir and find all we need.
    tool_names = ['substance3d_baker', 'sbscooker', 'sbsmutator', 'sbsrender']
    sample_dir_names = ['Sbs', 'Sbsar', 'Meshes', 'Template']

    base_resources_path = os.path.join(batchtools_path, 'resources/packages')
    #base_docs_path = os.path.join(os.path.expanduser('~/Documents'), os.path.basename(batchtools_path))
    base_docs_path = demos.get_sample_base_path()
    base_samples_path = base_docs_path # os.path.join(base_docs_path, 'samples')
    base_output_path = os.path.join(base_docs_path, 'samples_output')

    exe_path = {exe: os.path.join(batchtools_path, exe) for exe in tool_names}
    samples_path = {_dir: os.path.join(base_samples_path, _dir) for _dir in sample_dir_names}
    output_path = {_dir: os.path.join(base_output_path, _dir) for _dir in sample_dir_names}

    if not os.path.isdir(samples_path['Meshes']):
        print('This sample is unfortunately not avaialable in the indie packaging because of content rights.')
        print('We are working on a solution for this.')
        exit(0)

    sbs_template_path = os.path.join(samples_path['Template'], 'mesh_texturing_template.sbs')

    # Create the output folders
    if not os.path.exists(base_docs_path):
        raise OSError('User directory {} not found'.format(base_docs_path))

    for key, value in output_path.items():
        demos.ensure_directory_creation(value)


    # BAKE MAPS (Normal, ID, AO, Curvature, World space normal)
    # Bake normal maps from meshes detected (will collect low/high poly based on "_high" and "_low" suffix)
    batchtools.bake_normal_from_meshes_match_by_name(exe_path['substance3d_baker'], samples_path['Meshes'], '.FBX', '11', '11',output_path['Template'])
    # Bake ID maps from meshes detected (will collect low/high poly based on "_high" and "_low" suffix)
    batchtools.bake_id_from_meshes_match_by_name(exe_path['substance3d_baker'], samples_path['Meshes'], '.FBX', '11', '11', output_path['Template'])
    # Bake ao from low poly meshes detected (will collect .obj) and Normal maps (the mesh name must be the same)
    batchtools.bake_from_meshes_and_nrm(exe_path['substance3d_baker'], 'ambient-occlusion', samples_path['Meshes'], '.FBX', output_path['Template'], '.png', '11', '11', output_path['Template'])
    # Bake curvature from low poly meshes detected (will collect .obj) and Normal maps (the mesh name must be the same)
    batchtools.bake_from_meshes_and_nrm(exe_path['substance3d_baker'], 'curvature', samples_path['Meshes'], '.FBX', output_path['Template'], '.png', '11', '11', output_path['Template'])
    # Bake world space normal from low poly meshes detected (will collect .obj) and Normal maps (the mesh name must be the same)
    batchtools.bake_from_meshes_and_nrm(exe_path['substance3d_baker'], 'normal-world-space', samples_path['Meshes'], '.FBX', output_path['Template'], '.png', '11', '11', output_path['Template'])

    # Detect baked maps
    def detect_baked_maps(path_name, extension, recursive):
        detected_maps = batchtools.get_files_by_extension(path_name, extension, recursive)
        detected_maps_dict = {}
        final_dict = {}

        if detected_maps != None:
            for m in detected_maps:
                map_path = m
                map_name = os.path.split(m)[1]
                map_name_no_extension = os.path.splitext(map_name)[0]
                detected_maps_dict[map_name_no_extension] = map_path

            for k in detected_maps_dict:
                # Check if we get a low poly mesh
                    # Check if it already exists in our final listing
                    if final_dict.get(detected_maps_dict[k]) == None:
                        # Store the low poly path as key and high poly path as value
                        final_dict[k] = detected_maps_dict[k]
        return final_dict


    detected_baked_maps = detect_baked_maps(output_path['Template'], ".png", True)


    # CREATE "SPECIALIZED" SBS FILES
    def specialize_template(sbsmutator_path, sd_resources_path, template_path, meshes_path, meshes_extension, maps_dict, output_path, debug):
        detected_meshes = batchtools.get_files_by_extension(meshes_path, meshes_extension, True)
        template_name = os.path.split(template_path)[1]
        template_name_no_extension = os.path.splitext(template_name)[0]

        get_template_inputs_cmd = " ".join(['"' + sbsmutator_path + '"',
                                "info",
                                "--input", '"' + template_path + '"',
                                "--print-inputs"])
        #print(get_template_inputs_cmd)
        # Get info from substance template
        get_template_inputs = os.popen(get_template_inputs_cmd).read()
        proc = subprocess.Popen(get_template_inputs_cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        template_inputs = []
        #for word in out.split():
        for word in out.decode("UTF-8").split():
            # Get the input identifier
            if not word in ("INPUT","GRAYSCALE","COLOR","GRAPH-URL","pkg:///"+template_name_no_extension):
                template_inputs.append(word)


        if detected_meshes != None:
            for d in detected_meshes:
                # Check if it's a low poly
                if "_low" in d:
                    mesh_name = os.path.split(d)[1]
                    mesh_name_no_extension = os.path.splitext(mesh_name)[0]
                    connect_input_command = []
                    for image_input in template_inputs:
                        needed_map = mesh_name_no_extension + "_" + image_input
                        # If the map exists in maps_dict
                        if maps_dict.get(needed_map) != None:
                            connect_input_command += ["--connect-image", image_input+"@path@"+maps_dict[needed_map]+"@format@JPEG"]

                    if connect_input_command != []:
                        specialize_cmd = [sbsmutator_path,
                                           "edit",
                                           "--input", template_path,
                                           "--presets-path", sd_resources_path,
                                           "--quiet",
                                           "--output-name", mesh_name_no_extension,
                                           "--output-path", output_path] + connect_input_command

                        print("____________________")
                        print("Specializing " + template_name + " for " + mesh_name)
                        print("Command: " + batchtools.list_to_command_line(specialize_cmd))
                        batchtools.run_command_popen(specialize_cmd)


    # CREATE SBS FILES USING TEMPLATE
    specialize_template(exe_path['sbsmutator'], base_resources_path, sbs_template_path, samples_path['Meshes'],'.FBX', detected_baked_maps, output_path['Template'], True)


    # CREATE SBSAR FILES
    batchtools.cook_sbsar_files(exe_path['sbscooker'], base_resources_path, output_path['Template'], output_path['Template'])


    # RENDER SBSAR FILES
    batchtools.render_sbsar_files(exe_path['sbsrender'], output_path['Template'], '11', '11', output_path['Template'])
