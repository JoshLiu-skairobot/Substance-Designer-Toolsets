import os
import sys
import functools
try:
    from pysbs import context
    sbs_context = context.Context()
except:
    sbs_context = None
# Environment variables for the different components 
automation_toolkit_env = 'SDAPI_SATPATH' 
packages_env = 'SDAPI_SATPACKAGESPATH' 
samples_env = 'SDAPI_SATSAMPLESPATH' 



def is_directory(directory):
    """
    Validates that the directory provided is actually a directory
    
    :param directory: The directory to validate
    :type directory: string
    
    :raise: :class: argparse.ArgumentTypeError if param is not a directory 
    """
    if not os.path.isdir(directory):
        raise argparse.ArgumentTypeError("%s is not a directory" % directory)
    return directory

def add_default_arguments(parser):
    """
    Add a default command line options for samples to provide the path to
    the automation toolkit, samples_directory and packages directory.

    :param parser: The parser to add the command line options to 
    :type parser: argparse.ArgumentParser
    """
    parser.add_argument('-atk',
        '--automation-toolkit-directory', 
        metavar='automation_toolkit_directory', 
        type=is_directory, 
        nargs=1,
        required = False,
        help='Set path to the automation toolkit to use during processing')

    parser.add_argument('-sd',
        '--samples-directory', 
        metavar='samples_directory', 
        type=is_directory, 
        nargs=1,
        required = False,
        help='Set path to the sample content directory')

    parser.add_argument('-pd',
        '--packages-directory', 
        metavar='packages_directory', 
        type=is_directory, 
        nargs=1,
        required = False,
        help='Set path to the packages use during processing')

    parser.add_argument('-dp',
        '--debug-path-detection', 
        dest = 'debug_path_detection',
        action='store_const',
        const=True,
        default=False,
        required = False,
        help='Shows debug information when looking up directories')

def check_directory_valid(directory, known_files = []):
    """
    Validates that the directory provided is actually a directory and contains at
    least one of the files known to be in the directory

    :param directory: The directory to validate
    :type directory: string
    :param known_files: a list of files of which at leastone must be in the 
        directory for it to be considered valid
    :type known_files: [string]

    :return: bool, True if the check is successful, False if not 
    """
    if not os.path.isdir(directory):
        return False
    if len(known_files) == 0:
        return True
    for f in known_files:
        if os.path.isfile(os.path.join(directory, f)):
            return True
    return False


def log_verbose(operation, status, verbose):
    """ 
    Prints a log message for an operation if the verbose
    flag is set
    
    :param operation: The name of the operation currently going on
    :type operation: string
    :param status: Specific information of what is going on
    :type status: string
    :param verbose: Flag saying whether it should be written or ignored
    :type operation: bool
    """ 
    if verbose:
        print('%s: %s' % (operation, status))


def check_command_line_parameter(parameter, known_files, verbose, operation_name):
    """
    Checks if a command line path is valid and has one of the
    known files. Raises an exception if it's invalid

    :param parameter: the value from the args for the command line parameter check
    :type operation: [string]
    :param known_files: a list of files of which at leastone must be in the 
        directory for it to be considered valid
    :type known_files: [string]
    :param verbose: Flag saying whether to write log messages from this operation
    :type operation: bool
    :param operation: The name of the operation currently going on
    :type operation: string

    :return: string, a valid path if successful
    :raise: :class: IOError if the directory is not valid
    """
    log_verbose(operation_name, 'Checking command line parameter', verbose)
    if not parameter is None:
        path = parameter[0]
        if check_directory_valid(path, known_files):
            log_verbose(operation_name, 'Command line path %s valid. Done' % (path), verbose)
            return path
        else:
            log_verbose(operation_name, 'Command line path %s invalid' % (path), verbose)
            # Abort the process early, command line parameters shows a strong intention
            # and the user need to correct things if it's invalid
            raise IOError('Command line path not valid')


    log_verbose(operation_name, 'No path provided on command line', verbose)
    return None
    

def check_environment_variable(environment_variable, known_files, verbose, operation_name):
    """
    Checks if an environment variable string is a valid path and has one of the
    known files. Raises an exception if it's invalid

    :param environment_variable: the environment variable to check
    :type environment: string
    :param known_files: a list of files of which at leastone must be in the 
        directory for it to be considered valid
    :type known_files: [string]
    :param verbose: Flag saying whether to write log messages from this operation
    :type operation: bool
    :param operation: The name of the operation currently going on
    :type operation: string

    :return: string, a valid path if successful
    :raise: :class: IOError if the directory is not valid
    """
    log_verbose(operation_name, 'Checking Environment variable %s' % (environment_variable), verbose)
    if not os.environ.get(environment_variable) is None:
        path = os.environ.get(environment_variable)
        if check_directory_valid(path, known_files):
            log_verbose(operation_name, 'Environment varible path %s valid. Done' % (path), verbose)
            return path
        else:
            log_verbose(operation_name, 'Environment variable path %s invalid' % (path), verbose)
            # Abort the process early, environment variables shows a strong intention
            # and the user need to correct things if it's invalid
            raise IOError('Environment variable path not valid')

    log_verbose(operation_name, 'No environment variable found', verbose)
    return None

def check_known_path(path, known_files, verbose, operation_name):
    """
    Checks if a path is a valid and has one of the
    known files. 

    :param path: the path to check
    :type environment: string
    :param known_files: a list of files of which at leastone must be in the 
        directory for it to be considered valid
    :type known_files: [string]
    :param verbose: Flag saying whether to write log messages from this operation
    :type operation: bool
    :param operation: The name of the operation currently going on
    :type operation: string

    :return: string, a valid path if successful, otherwise None
    """
    log_verbose(operation_name, 'Checking known path %s' % (path), verbose)
    if (not path is None) and check_directory_valid(path, known_files):
        log_verbose(operation_name, 'path %s valid. Done' % (path), verbose)
        return path
    log_verbose(operation_name, 'path invalid %s' % (path), verbose)
    return None

def run_fn_list(fn_list):
    """
    Runs a list of functions with zero parameters returns when it hits a
    function returning something else than None

    :param fn_list: a list of functions to call
    :type fn_list: [fn()]
    
    :return: first non-None result from the functions, None if no function returns a valid result
    """
    result = None
    for f in fn_list:
        result = f()
        if not result is None:
            return result
    return None

def get_current_file_directory():
    return os.path.dirname(os.path.abspath(__file__))

def get_automation_toolkit_directory(args):
    """
    Read out automation toolkit directory
    Search order is:
    1. Command line parameter automation_toolkit_directory
    2. Environment variable, SDAPI_SATPATH
    3. SbsPy location (if available)
    4. Known good locations based on current platform
    
    :param args: parsed arguments from argparse
    :type args: class

    :return: string, The path to the first found automation toolkit directory
    :raise: :class: IOError if nothing found or invalid directories are specified
    """
    known_files = ['sbsrender', 'sbsrender.exe']
    operation = 'Detecting automation toolkit'
    verbose = args.debug_path_detection 
    # Locations to check
    detection_operations = [
        functools.partial(check_command_line_parameter, args.automation_toolkit_directory, known_files, verbose, operation),
        functools.partial(check_environment_variable, automation_toolkit_env, known_files, verbose, operation),
        functools.partial(check_known_path, sbs_context.getAutomationToolkitInstallPath(), known_files, verbose, operation),
        functools.partial(check_known_path, os.path.join(get_current_file_directory(), '..'), known_files, verbose, operation),
        functools.partial(check_known_path, os.path.join('c:\\Program Files', 'Allegorithmic', 'Substance Automation Toolkit'), known_files, verbose, operation),
        functools.partial(check_known_path, os.path.join('/Applications', 'Substance Automation Toolkit'), known_files, verbose, operation)
    ]
    # Check all operations until we find a non-None path

    path = run_fn_list(detection_operations)
    if path is None:
        # None of our options worked, Raise an Exception
        raise IOError('Could not find substance automation toolkit installation location.\
                       Use command line parameter %s or environment variable %s to set it explicitly' % ('--automation_toolkit_directory', automation_toolkit_env))
    return path




def get_automation_toolkit_packages_directories(args):
    """
    Try to find the path to the root of the samples based on
    a set of different location
    Search order is:
    1. Command line parameter packages-directory
    2. Environment variable, SDAPI_SATPACKAGESPATH
    3. SbsPy location (if available)
    4. Likely to be good location based on various platforms

    :param args: parsed arguments from argparse
    :type args: class

    :return: string, The path to the first found automation toolkit packages directory
    :raise: :class: IOError if nothing found or invalid directories are specified
    """

    known_files = ['ambient_occlusion.sbs']
    operation = 'Detecting packages directory'
    verbose = args.debug_path_detection 

    # Locations to check
    detection_operations = [
        functools.partial(check_command_line_parameter, args.packages_directory, known_files, verbose, operation),
        functools.partial(check_environment_variable, packages_env, known_files, verbose, operation),
        functools.partial(check_known_path, context.Context.getDefaultPackagePath(), known_files, verbose, operation),
        functools.partial(check_known_path, os.path.join(get_current_file_directory(), '..', 'resources', 'packages'), known_files, verbose, operation),
        functools.partial(check_known_path, os.path.join('c:\\Program Files', 'Allegorithmic', 'Substance Automation Toolkit', 'resources', 'packages'), known_files, verbose, operation),
        functools.partial(check_known_path, os.path.join('/Applications', 'Substance Automation Toolkit', 'resources', 'packages'), known_files, verbose, operation)
    ]

    path = run_fn_list(detection_operations)
    if path is None:
        # None of our options worked, Raise an Exception
        raise IOError('Could not find substance automation toolkit samples location.\
                       Use command line parameter %s or environment variable %s to set it explicitly' % ('--automation_toolkit_directory', packages_env))
    return path


def get_automation_toolkit_samples_directory(args):
    """
    Try to find the path to the root of the samples based on
    a set of different location
    Search order is:
    1. Command line parameter samples-directory
    2. Environment variable, SDAPI_SATSAMPLESPATH
    3. Relative to the location of this script
    :param args: parsed arguments from argparse
    :type args: class

    :return: string, The path to the first found automation toolkit directory
    :raise: :class: IOError if nothing found or invalid directories are specified
    """
    known_files = ['demos.py']
    operation = 'Detecting samples directory'
    verbose = args.debug_path_detection 

    # Locations to check
    detection_operations = [
        functools.partial(check_command_line_parameter, args.samples_directory, known_files, verbose, operation),
        functools.partial(check_environment_variable, samples_env, known_files, verbose, operation),
        functools.partial(check_known_path, get_current_file_directory(), known_files, verbose, operation),
    ]

    path = run_fn_list(detection_operations)
    if path is None:
        # None of our options worked, Raise an Exception
        raise IOError('Could not find substance automation toolkit samples location.\
                       Use command line parameter %s or environment variable %s to set it explicitly' % ('--automation_toolkit_directory', samples_env))
    return path
