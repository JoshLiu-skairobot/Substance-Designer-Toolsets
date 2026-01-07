import argparse
import os
import demo_cmd
import demos
import functools
import multiprocessing
import batchtools_utilities
import create_compositing_network as comp
import sys
from pysbs import context
from pysbs import api_helpers
from pysbs import batchtools

__copyright__ = '@copyright Allegorithmic. All rights reserved.'
__author__ = 'david.larsson@allegorithmic.com'
VERSION = 'Texturing demo script 1.0'


def attrib_vec(name_value_pair):
    """
    Generates a string command line parameter string for sbsrender

    :param name_value_pair: name and value of the parameter set as a tuple
    :type name_value_pair: (string, [val])
    :return: string The parameter merged with its value in a batch processor compatible way
    """
    return '%s@%s' % name_value_pair


def generate_bake_output_name(source_file, baker_name):
    """
    Generates the filename for a baked file

    :param source_file: The mesh to be baked
    :type source_file: string
    :param baker_name: The name of the baker
    :type baker_name: string
    :return: string
    """
    return '%s_%s' % (api_helpers.splitExtension(source_file)[0], baker_name)


def generate_texture_bindings(source_file, maps_to_bake, texture_path):
    """
    Generates a dictionary from input node names to filenames of baked textures
    to simplify binding the right texture file to the right input when rendering a
    Substance

    :param source_file: The mesh being baked
    :type source_file: string
    :param maps_to_bake: map_to_bake: a vector of tuples with pass name, parameters and input to bind it to
    :type maps_to_bake: (string, string, string)
    :param texture_path: The location of the textures baked
    :type texture_path: string
    :return: dictionary
    """
    results = {}
    for bake_pass, _, var in maps_to_bake:
        results[var] = os.path.join(texture_path, generate_bake_output_name(source_file, bake_pass) + '.png')
    return results


def bake(src_mesh, map_to_bake, parameters, resolution, output_path):
    """
    Bakes a map for a mesh

    :param src_mesh: path to the mesh to bake
    :type src_mesh: string
    :param map_to_bake: The name of the map to bake
    :type map_to_bake: string
    :param parameters: command line parameters to append to the bake command line
    :type parameters: [string]
    :param resolution: The resolution to bake expressed as N in 2^N. Applies to both width and height
    :type resolution: int
    :param output_path: The target directory for the baked map
    :type output_path: string
    :return: None
    """
    bake_function = ('sbsbaker_' + map_to_bake).replace('-', '_')
    bake_command = getattr(batchtools, bake_function, None)
    if bake_command is None:
        raise BaseException('Failed to find command command for baker %s' % map_to_bake)
    sys.stdout.write('Baking %s\n' % os.path.basename(generate_bake_output_name(src_mesh, map_to_bake)))
    bake_command(inputs=src_mesh,
                 output_size=(resolution, resolution),
                 output_path=output_path,
                 output_name=generate_bake_output_name(src_mesh, map_to_bake),
                 **parameters).wait()


def cook(src_file, resources_path, output_path):
    """
    Cooks an sbsfile to an sbsar file

    :param src_file: path to the sbs file to cook
    :type src_file: string
    :param resources_path: The path to the substance resources
    :type resources_path: string
    :param output_path: The directory to put the result
    :type output_path: string
    :return: None
    """
    sys.stdout.write('Cooking %s\n' % os.path.basename(src_file))
    batchtools.sbscooker(inputs=src_file,
                         output_path=output_path,
                         includes=resources_path,
                         quiet=True).wait()


def render_maps(variation_name, input_bindings, sbsar_file, output_size, output_path, use_gpu_engine):
    """
    Invokes sbsrender to render out maps for a material with a set of parameters

    :param variation_name: name of the variation being rendered
    :type variation_name: string
    :param input_bindings: a list of tuples with input image names and textures to bind to them
    :type input_bindings: {string : string}
    :param sbsar_file: The sbsar file to render
    :type sbsar_file: string
    :param output_size: the output size for the rendered image. In format 2^n where n is the parameter
    :type output_size: int
    :param output_path: The directory to put the result
    :type output_path: string
    :param use_gpu_engine: Use GPU engine when rendering
    :type use_gpu_engine: bool

    :return: None
    """
    values = ['$outputsize@%d,%d' % (output_size, output_size)]
    bindings = list(map(attrib_vec, input_bindings.items()))

    engine_params = {'engine': batchtools_utilities.get_gpu_engine_for_platform()} if use_gpu_engine else {}
    sys.stdout.write('Rendering outputs for %s variation: %s\n' % (os.path.basename(sbsar_file), variation_name))
    batchtools.sbsrender_render(inputs=sbsar_file,
                                output_path=output_path,
                                output_name='%s_{outputNodeName}' % variation_name,
                                set_value=values,
                                set_entry=bindings,
                                **(engine_params)).wait()


# All bakes needed for generating materials together with
# additional command line options and
# what input images they should be bound to when rendering
maps_to_bake = [('ambient-occlusion', {}, 'ambient-occlusion'),
                ('curvature', {}, 'curvature'),
                ('position', {}, 'position'),
                ('normal-world-space', {}, 'normal-world-space'),
                # Bake color from mesh with submesh id as color source (2)
                ('color-from-mesh', {'use-lowdef-as-highdef': 'true', 'color-source': '3'}, 'color-id')]

# Dictionary mapping sub mesh to a compositing color
submesh_to_color_mapping = {'head': '0,1,0',
                            'body': '0,0,1',
                            'base': '1,0,0'}

# SBS assignments for all variations to render together
# with what sub graph to render and parameters to set for each material
output_texture_variations = {'Rusty':
                                 {'head': ('steel_battered.sbs', 'steel_rusty', {'rust_spreading': [.16],
                                                                                 'steel_color': [1, .88, .60]}),
                                  'body': ('steel_battered.sbs', 'steel_rusty', {'rust_spreading': [.16],
                                                                                 'steel_color': [.98, .81, .75]}),
                                  'base': ('steel_battered.sbs', 'steel_rusty', {'rust_spreading': [.16]})},
                             'Leather':
                                 {'head': ('leather_fine_touch.sbs', 'leather_worn', {}),
                                  'body': ('leather_fine_touch.sbs', 'leather_worn', {}),
                                  'base': ('leather_fine_touch.sbs', 'leather_worn', {})},
                             'Painted_Terracotta':
                                 {'head': ('terracotta_glossy.sbs', 'painted_terracotta', {}),
                                  'body': ('terracotta_glossy.sbs', 'painted_terracotta', {}),
                                  'base': ('terracotta_glossy.sbs', 'painted_terracotta', {})}
                             }


def main():
    # Set up command line parser to allow paths to various resources to
    # be controlled by the command line
    parser = argparse.ArgumentParser('Texture Mat')
    demo_cmd.add_default_arguments(parser)

    # Add example specific parameters to the command line
    parser.add_argument('--resolution',
                        type=int,
                        default=10,
                        help='Sets the output resolution for the maps as 2^resolution')
    parser.add_argument('--source-mesh',
                        default=os.path.join('texture_mat', 'Mesh_MAT.FBX'),
                        help='Sets the mesh to bake maps from')
    parser.add_argument('--disable-bake-maps',
                        action='store_true',
                        help='Flag to disable baking geometry maps')

    parser.add_argument('--use-gpu-engine',
                        dest='gpu_engine',
                        action='store_true',
                        help='Make sbsrender use the gpu engine')
    parser.set_defaults(gpu_engine=False)

    # Parse command line and pull out the paths for the different
    # locations used
    args = parser.parse_args()
    atk_dir = demo_cmd.get_automation_toolkit_directory(args)
    samples_dir = demo_cmd.get_automation_toolkit_samples_directory(args)
    packages_dir = demo_cmd.get_automation_toolkit_packages_directories(args)

    sbs_context = context.Context()
    sbs_context.setAutomationToolkitInstallPath(atk_dir)
    sbs_context.setDefaultPackagePath(packages_dir)

    # Create the data path
    data_path = os.path.join(samples_dir, 'texture_mat')

    # Create the output path
    output_path = os.path.join(data_path, '_output')

    # Resolution for the output 2 ^ output_size is the actual value
    output_size = args.resolution

    # Make sure the output directory exist
    demos.ensure_directory_creation(output_path)

    src_mesh = args.source_mesh

    # Number of parallell jobs to process
    # Guess to allow some parallell processing to hide IO and sequential steps
    # together with not maxing out all cpu's to allow parallell processes to
    # use more than one core
    thread_count = max(multiprocessing.cpu_count() // 2, 1)

    if not args.disable_bake_maps:
        # Bake all maps needed
        bake_task_list = []
        for current_map, parameters, _ in maps_to_bake:
            bake_task_list.append(functools.partial(bake, src_mesh, current_map, parameters, output_size, output_path))
        # Start multithreaded baking
        batchtools_utilities.run_tasks(bake_task_list, thread_count)

    compositing_network_filenames = {}

    # Create a compositing network for each variation specified
    for variation, assignments in output_texture_variations.items():
        submesh_assignments = {}
        for (submesh, (sbs_file, sub_material, parameters)) in assignments.items():
            submesh_assignments[submesh] = {'mask_color': submesh_to_color_mapping[submesh],
                                            'substance': os.path.join(data_path, sbs_file),
                                            'graph_name': sub_material,
                                            'parameters': parameters}
        compositing_network_filename = os.path.join(output_path, variation + '_compositing.sbs')
        compositing_network_filenames[variation] = compositing_network_filename
        comp.create_compositing_network(sbs_context, submesh_assignments, .1, compositing_network_filename)

    # Cook all compositing networks
    cook_task_list = []
    for _, filename in compositing_network_filenames.items():
        cook_task_list.append(functools.partial(cook, filename, packages_dir, output_path))

    # Start multithreaded cooking
    batchtools_utilities.run_tasks(cook_task_list, thread_count)

    # Render maps for all variations
    variation_task_list = []
    for variation_name, _ in output_texture_variations.items():
        # Build path for the sbsar file to use
        sbsar_file = compositing_network_filenames[variation_name] + 'ar'

        # Figure out what maps should be bound to what input images
        bake_bindings = generate_texture_bindings(src_mesh, maps_to_bake, output_path)
        variation_task_list.append(functools.partial(render_maps,
                                                     variation_name,
                                                     bake_bindings,
                                                     sbsar_file,
                                                     output_size,
                                                     output_path,
                                                     args.gpu_engine))

    # Start multithreaded rendering of variations
    batchtools_utilities.run_tasks(variation_task_list, thread_count)


if __name__ == "__main__":
    main()
