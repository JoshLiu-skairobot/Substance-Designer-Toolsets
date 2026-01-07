import argparse
import batchtools_utilities
import demos
import demo_cmd
import functools
import multiprocessing
import os
import random as rd
import sys

try:
    if sys.version_info.major == 2:
        import Queue as queue
    elif sys.version_info.major == 3:
        import queue
except ImportError as e:
    raise e.message

from pysbs import context
from pysbs import batchtools

__copyright__ = '@copyright Allegorithmic. All rights reserved.'
__author__ = 'david.larsson@allegorithmic.com'
VERSION = 'Variations demo script 1.0'

# Definition of all materials to generate permutations of
materials = {
    'opus': {
        'sbs_file': 'opus.sbs',
        'params': {
            'pattern_selection': ('random_int', [1], [5]),
            'x_amount': ('random_int', [5], [10]),
            'y_amount': ('random_int', [5], [10]),
            'crack_scale': ('random_int', [2], [4]),
        }
    }

}


def stable_rand_int(a, b):
    """
    Generates a random integer between a (inclusive) and b (inclusive).
    For some reason random.randomint changes the random seed differently between
    Python 2.7 and 3.5 but random.uniform seems to behave consistently

    :param a: minimum value for the random number
    :type a: int 
    :param b: maximum value for the random number
    :type b: int

    :return: a random integer
    """
    assert (b >= a)
    assert (abs(a) < 100000)
    assert (abs(b) < 100000)
    return a + int(rd.uniform(0, b - a + .999))
    # return rd.randrange(a, b + 1)


def instantiate_vector(_range, permutation, permutation_count):
    """
    Generates a set of values based

    :param _range: Tuple representing the operation, the minimum and maximum value
        Valid operations are
        'random': Random value between min and max
        'random_int': Random value between min and max clamped to an integer
        'linear': linear ramp between min and max based on the permutation and permuation_count
    :type _range: (string, [minX, minY, ...], [maxX, maxY, ...])
    :param permutation: Current permutation
    :type permutation: int
    :param permutation_count: Total number of permutation
    :type permutation_count: int

    :return: [] vector of values based on the _range parameter
    """
    operation = _range[0]
    _min = _range[1]
    _max = _range[2]
    res = []
    for i in range(0, len(_min)):
        if operation == 'random':
            res.append(rd.uniform(_min[i], _max[i]))
        elif operation == 'random_int':
            res.append(int(stable_rand_int(_min[i], _max[i])))
        elif operation == 'linear':
            val = _min[i] + (_max[i] - _min[i]) * (float(permutation) / float(permutation_count - 1))
            res.append(val)
        else:
            raise BaseException('Invalid operation %s' % operation)
    return res


def instantiate_params(params, permutation, permutation_count):
    """
    Generates a set of instantiations of parameters
    :param params: Dictionary of named parameters. For representation of parameters see documentation
        for instantiate_vector
    :type params: {string: (string, [minX, minY, ...], [maxX, maxY, ...]) }
    :param permutation: Current permutation
    :type permutation: int
    :param permutation_count: Total number of permutation
    :type permutation_count: int

    :return: {string: (string, [minX, minY, ...], [maxX, maxY, ...]) }
        Dictionary of keys with values for instantiated parameters
    """
    return {k: instantiate_vector(v, permutation, permutation_count) for k, v in sorted(params.items())}


def param_vec(name_value_pair):
    """
    Generates a string command line parameter string for sbsrender

    :param name_value_pair: name and value of the parameter set as a tuple
    :type name_value_pair: (string, [val])
    :return: string The parameter merged with its value in a batch processor compatible way
    """
    name, value = name_value_pair
    return ('%s@' % name) + ','.join(map(str, value))


def strip_path_and_ext(src_file):
    """
    Strips the path and extention from a filename

    :param src_file: The filename to strip
    :type src_file: string

    :return: string, the stripped filename
    """
    root_name = os.path.splitext(os.path.split(src_file)[1])[0]
    return root_name


def render_maps(material_name, output, params, permutation, sbsar_file, output_size, output_path, use_gpu_engine,
                random_seed):
    """
    Invokes sbsrender to render out maps for a material with a set of parameters

    :param material_name: name of the material being rendered
    :type material_name: string
    :param output: name of the output node to be rendered
    :type output: string
    :param params: Instantiated parameters
    :type params: {string: [...]}
    :param permutation: Current permutation
    :type permutation: int
    :param sbsar_file: The sbsar file to render
    :type sbsar_file: string
    :param output_size: the output size for the rendered image. In format 2^n where n is the parameter
    :type output_size: int
    :param output_path: The directory to put the result
    :type output_path: string
    :param use_gpu_engine: Use GPU engine when rendering
    :type use_gpu_engine: bool
    :param random_seed: The random seed to use for the substance when rendering it
    :type random_seed: int


    :return: None
    """
    values = ['$outputsize@%d,%d' % (output_size, output_size),
              '$randomseed@%d' % random_seed] + list(map(param_vec, params.items()))
    engine_params = {'engine': batchtools_utilities.get_gpu_engine_for_platform()} if use_gpu_engine else {}
    output_name = '%s_%s_%d' % (output, material_name, permutation)
    sys.stdout.write('Rendering %s\n' % output_name)
    batchtools.sbsrender_render(inputs=sbsar_file,
                                output_path=output_path,
                                output_name=output_name,
                                input_graph_output=output,
                                set_value=values,
                                **(engine_params)).wait()


def instantiate(material_name, params, permutation, sbsar_file, output_path):
    """
    Invokes sbsmutator to create an sbs file with defaults changed
    to represent the parameters

    :param material_name: name of the material being instantiated
    :type material_name: string
    :param params: Instantiated parameters
    :type params: {string: [...]}
    :param permutation: Current permutation
    :type permutation: int
    :param sbsar_file: The sbsar file to instantiate
    :type sbsar_file: string
    :param output_path: The directory to put the result
    :type output_path: string

    :return: None
    """
    output_name = '%s_%d' % (material_name, permutation)
    sys.stdout.write('Instantiating %s\n' % output_name)
    default_values = list(map(param_vec, params.items()))
    batchtools.sbsmutator_instantiate(input=sbsar_file,
                                      output_path=output_path,
                                      output_name=output_name,
                                      set_default_value=default_values).wait()


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
    sys.stdout.write('Cooking %s\n' % src_file)
    batchtools.sbscooker(inputs=src_file,
                         output_path=output_path,
                         includes=resources_path,
                         quiet=True).wait()


def main():
    # Set up command line parser to allow paths to various resources to
    # be controlled by the command line
    parser = argparse.ArgumentParser('Variations')
    demo_cmd.add_default_arguments(parser)
    # Add variations specific parameters
    parser.add_argument('--permutation-count',
                        type=int,
                        default=10,
                        help='Sets the number of permutations to make from the source SBS')

    parser.add_argument('--resolution',
                        type=int,
                        default=10,
                        help='Sets the the output resolution for the maps as 2^resolution')

    parser.add_argument('--use-gpu-engine',
                        dest='gpu_engine',
                        action='store_true',
                        help='Make sbsrender use the gpu engine')
    parser.set_defaults(gpu_engine=False)

    args = parser.parse_args()
    atk_dir = demo_cmd.get_automation_toolkit_directory(args)
    samples_dir = demo_cmd.get_automation_toolkit_samples_directory(args)
    packages_dir = demo_cmd.get_automation_toolkit_packages_directories(args)

    # Use the python api to find the command line tools
    sbs_context = context.Context()
    sbs_context.setAutomationToolkitInstallPath(atk_dir)
    sbs_context.setDefaultPackagePath(packages_dir)

    # Hardcoded path to where the data for this demo is located
    # Assuming it's being run from the scripts folder
    # We should make this
    data_path = os.path.join(samples_dir, 'variations')

    output_path = os.path.join(data_path, '_output')

    # The number of permutations to generate
    permutation_count = args.permutation_count

    # Resolution for the output 2 ^ output_size is the actual value
    output_size = args.resolution

    # Set random seed if you want the generation to be deterministic
    rd.seed(0xc0ffee)

    # Make sure the output directory exist
    demos.ensure_directory_creation(output_path)

    # Task list for multi threaded processing
    task_list = []

    # Outputs to render
    outputs = ['basecolor', 'normal', 'roughness']

    # Loop over all materials
    for material_name, data in materials.items():
        # Cook the sbs file to an sbsar file that can be rendered
        sbs_file = os.path.join(data_path, data['sbs_file'])

        # Note, we don't put the cook job in the task queue since
        # the other jobs are dependent on this job finishing
        cook(sbs_file, packages_dir, output_path)
        sbsar_file = os.path.join(output_path, strip_path_and_ext(sbs_file) + '.sbsar')
        # Generate all permutations
        for i in range(0, permutation_count):
            # Instantiate parameters
            params = instantiate_params(data['params'], i, permutation_count)

            # Generate the random seed for this permutation
            random_seed = stable_rand_int(0, 10000)

            # Add a task for rendering images
            for o in outputs:
                task_list.append(functools.partial(render_maps,
                                                   material_name,
                                                   o,
                                                   params,
                                                   i,
                                                   sbsar_file,
                                                   output_size,
                                                   output_path,
                                                   args.gpu_engine,
                                                   random_seed))
            # Add a task for generating a substance files with the parameters as default
            task_list.append(functools.partial(instantiate,
                                               material_name,
                                               params,
                                               i,
                                               sbsar_file,
                                               output_path))

    # Number of parallell jobs to process
    # Guess to allow some parallell processing to hide IO and sequential steps
    # together with not maxing out all cpu's to allow parallell processes to
    # use more than one core
    thread_count = max(multiprocessing.cpu_count() // 2, 1)

    batchtools_utilities.run_tasks(task_list, thread_count)


if __name__ == "__main__":
    main()
