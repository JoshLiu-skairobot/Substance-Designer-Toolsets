from collections import OrderedDict
import sys
import os
from pysbs import context
from pysbs import sbsenum
from pysbs import sbsgenerator
from pysbs import autograph

__copyright__ = '@copyright Allegorithmic. All rights reserved.'
__author__ = 'david.larsson@allegorithmic.com'
VERSION = 'Compositing demo script 1.0'


def make_sbs_path(path):
    """
    Cleans up a file path for using it in Pysbs

    :param path: The path to proecess
    :type path: string
    :return: string transformed path
    """
    return path.replace('\\', '/').strip('\"')


def get_color_mode_from_input_name(input_name):
    """
    Figures out whether an input texture is grayscale or color
    based on its name. Note, this is very hacky and should be done using
    metadata about the pass or file information

    :param input_name: name of the input
    :type input_name: string
    :return: sbsenum.ColorModeEnum COLOR or GRAYSCALE based on the name
    """
    if ('curvature' in input_name) or ('ambient-occlusion' in input_name):
        return sbsenum.ColorModeEnum.GRAYSCALE
    else:
        return sbsenum.ColorModeEnum.COLOR


def create_compositing_network(context, material_mappings, fuzziness, output_file):
    """
    Creates a compositing network where materials are associated with colors and
    parameters are set on the ingoing materials

    :param context: Pysbs context to create the node in
    :type path: Pysbs.context.Context
    :param material_mappings: A dictionary with named submeshes with path to the sbs file, name of the graph, the color to use for compositing, and parameters to set 
    :type material_mappings: dictionary
    :param fuzziness: the fuzziness to use for the multi_material_blend node doing the work
    :type fuzziness: float
    :param output_file: The name of the file to write
    :type output_file: string
    :return: None
    """

    # The channels we generate outputs for
    channels = OrderedDict([
        ('basecolor', {'usage': sbsenum.UsageEnum.BASECOLOR}),
        ('roughness', {'usage': sbsenum.UsageEnum.ROUGHNESS}),
        ('metallic', {'usage': sbsenum.UsageEnum.METALLIC}),
        ('normal', {'usage': sbsenum.UsageEnum.NORMAL}),
        ('height', {'usage': sbsenum.UsageEnum.HEIGHT}),
    ])

    # Mapping between a channel name and multi material blend output
    channel_to_multi_material_blend = {
        'basecolor': 'basecolor',
        'roughness': 'Roughness',
        'metallic': 'Metallic',
        'normal': 'Normal',
        'height': 'Height',
    }

    # Create a document with a Composite graph in
    sbsDoc = sbsgenerator.createSBSDocument(context,
                                            aFileAbsPath=output_file,
                                            aGraphIdentifier='Composite')

    # Get the graph 'Composite' graph
    aGraph = sbsDoc.getSBSGraph(aGraphIdentifier='Composite')

    channel_to_output_mapping = {
        channel_name: aGraph.createOutputNode(aIdentifier=channel_name,
                                              aUsages={
                                                  channel_properties['usage']: {sbsenum.UsageDataEnum.COMPONENTS: sbsenum.ComponentsEnum.RGBA}
                                              })
        for i, (channel_name, channel_properties) in enumerate(channels.items())
    }

    # Set up the material id colors to use for the compositing network
    material_count = len(material_mappings)
    material_colors = {}

    # Sort the material mappings to make sure they are
    # Generated in the same order every time if the inputs are the same
    # Regardless of how python lays out the map
    sorted_material_mappings = sorted(material_mappings.items())
    for (idx, (material_id, settings)) in enumerate(sorted_material_mappings):
        material_colors['Material_%d_Color' % (idx + 2)] = settings['mask_color']
        material_colors['Material_%d_Fuzziness' % (idx + 2)] = fuzziness

    # Create the parameters for the multi_material_blend so it outputs the right
    # channels
    composer_params = {'diffuse': 'diffuse' in channels,
                       'basecolor': 'basecolor' in channels,
                       'normal': 'normal' in channels,
                       'specular': 'specular' in channels,
                       'emissive': 'emissive' in channels,
                       'glossiness': 'glossiness' in channels,
                       'roughness': 'roughness' in channels,
                       'metallic': 'metallic' in channels,
                       'specularlevel': 'specularlevel' in channels,
                       'ambient_occlusion': 'ambient_occlusion' in channels,
                       'height': 'height' in channels,
                       'opacity': 'opacity' in channels,
                       'Materials': material_count + 1}
    composer_params.update(material_colors)

    # Create multi_material_blend node
    composer = aGraph.createCompInstanceNodeFromPath(sbsDoc, aPath='sbs://multi_material_blend.sbs',
                                                     aParameters=composer_params)

    # Connect the compositing outputs to their respective Output node
    for channel_name, output_node in channel_to_output_mapping.items():
        aGraph.connectNodes(aLeftNode=composer,
                            aRightNode=output_node,
                            aLeftNodeOutput=channel_to_multi_material_blend[channel_name])

    # Create the ingoing materials and set parameters for them
    material_nodes = []
    all_material_inputs = {}

    for _, material_data in sorted_material_mappings:
        # Create path for importing the right substance file and the right node
        sbs_path = make_sbs_path(material_data['substance']) + '/' + material_data['graph_name']

        # Create the new material node
        node = aGraph.createCompInstanceNodeFromPath(sbsDoc,
                                                     aPath=sbs_path,
                                                     aParameters=material_data['parameters'])

        # Save the node for later use
        material_nodes.append(node)

        # store away all material input images so we can
        # export one input representing all materials
        # sharing that input
        inputs = node.getDefinition().mInputs
        for i in inputs:
            if i.mIdentifier in all_material_inputs:
                all_material_inputs[i.mIdentifier].append(node)
            else:
                all_material_inputs[i.mIdentifier] = [node]

    # Connect all source material outputs to the compositing node
    for i, material_node in enumerate(material_nodes):
        for c in channels.keys():
            # Use material 0 as default material as well
            if i == 0:
                aGraph.connectNodes(aLeftNode=material_node, aRightNode=composer, aLeftNodeOutput=c,
                                    aRightNodeInput='material%d_%s' % (i + 1, c))
            aGraph.connectNodes(aLeftNode=material_node, aRightNode=composer, aLeftNodeOutput=c,
                                aRightNodeInput='material%d_%s' % (i + 2, c))

    # Create input nodes for all material inputs
    # and wire them up to the corresponding inputs on the materials by name
    for i, (input_name, nodes) in enumerate(sorted(all_material_inputs.items())):
        color_mode = get_color_mode_from_input_name(input_name)
        input_node = aGraph.createInputNode(aIdentifier=input_name,
                                            aColorMode=color_mode)
        for node in nodes:
            aGraph.connectNodes(aLeftNode=input_node, aRightNode=node, aRightNodeInput=input_name)

    # Create an input for the mask
    input_mask = aGraph.createInputNode(aIdentifier='color-id')

    # connect the mask input to the color id
    aGraph.connectNodes(aLeftNode=input_mask, aRightNode=composer, aRightNodeInput='Input_160')

    # Layout the nodes
    autograph.layoutGraph(aGraph)

    # Write the document to destination .sbs file
    sbsDoc.writeDoc()
    sys.stdout.write("Resulting substance saved at %s\n" % os.path.basename(output_file))
