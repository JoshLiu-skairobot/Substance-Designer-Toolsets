import argparse
import os

from pysbs import context
from pysbs import sbsenum
from pysbs import sbsgenerator
from pysbs import autograph as ag

import demo_cmd
import demos


def create_base_network(graph, doc):
    """
    Creates a network consisting of a base color output, a pixel processor and a wood material

    :param graph: The graph to create the network in
    :type graph: pysbs.graph.graph.SBSGraph
    :param doc: The document to create the network in
    :type doc: pysbs.substance.substance.SBSDocument
    :return: The pixel processor node of the network 
    """
    # Create an output BaseColor node
    outBaseColor = graph.createOutputNode(aIdentifier='BaseColor',
                                          aUsages={sbsenum.UsageEnum.BASECOLOR: {sbsenum.UsageDataEnum.COMPONENTS: sbsenum.ComponentsEnum.RGBA}})

    # Create pixelprocessor
    pp_node = graph.createCompFilterNode(sbsenum.FilterEnum.PIXEL_PROCESSOR)
    # Connect the pixel processor node to the BaseColor
    graph.connectNodes(aLeftNode=pp_node, aRightNode=outBaseColor)

    # Instantiate a wood material for the raytracer
    wood = graph.createCompInstanceNodeFromPath(doc, aPath='sbs://materials/pbr/wood_american_cherry.sbs')
    # Connect base color and roughness from the wood to the pixel processor
    graph.connectNodes(aLeftNode=wood, aRightNode=pp_node)
    graph.connectNodes(aLeftNode=wood, aRightNode=pp_node, aRightNodeInput='input:1', aLeftNodeOutput='roughness')

    # Layout the graph
    ag.layoutGraph(graph)

    return pp_node


def sphere_uv(fn):
    """
    Substance function for generating a uv coordinate from a sphere normal and a tiling factor

    :param fn: The function context to create the function in
    :type fn: FunctionContext
    :return: function, a function to call to instantiate the function 
    """
    normal = fn.input_parameter('normal', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    tiling = fn.input_parameter('tiling', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT1)
    fn_pi = fn.import_external_function('sbs://functions.sbs/Functions/Math/Pi')

    pi = fn_pi()
    two_pi = pi * 2.0
    u = (fn.atan2(fn.expand(normal[0], normal[2])) + pi) / two_pi
    v = fn.atan2(fn.expand(1.0, normal[1])) / pi
    uv = fn.expand(u * tiling, v * tiling)
    return fn.generate(uv)


def phong_lighting(fn):
    """
    Computes phong shading for a point and a light source

    :param fn: The function context to create the function in
    :type fn: FunctionContext
    :return: function, a function to call to instantiate the function 
    """
    normal = fn.input_parameter('normal', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    base_color = fn.input_parameter('base_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    specular_color = fn.input_parameter('specular_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    roughness = fn.input_parameter('roughness', sbsenum.WidgetEnum.COLOR_FLOAT1)
    cam_dir = fn.input_parameter('cam_dir', sbsenum.WidgetEnum.COLOR_FLOAT3)
    light_dir = fn.input_parameter('light_dir', sbsenum.WidgetEnum.COLOR_FLOAT3)

    fn_pi = fn.import_external_function('sbs://functions.sbs/Functions/Math/Pi')
    fn_pow = fn.import_external_function('sbs://functions.sbs/Functions/Math/Pow')

    epsilon = .00001
    spec_magic_number = 20.0

    pi = fn_pi()

    h = cam_dir + light_dir
    h = fn.normalize(h)
    nDotL = fn.max_of(fn.dot(light_dir, normal), epsilon)
    nDotH = fn.max_of(fn.dot(h, normal), 0.0)
    n = spec_magic_number / (roughness + epsilon)
    out_d = base_color * nDotL
    s_norm = (n + 8.0) / (8.0 * pi)

    out_s = specular_color * fn_pow(nDotH, n) * s_norm
    out_col = out_s + out_d
    return out_col


def ambient_lighting(fn):
    """
    Computes ambient lighting

    :param fn: The function context to create the function in
    :type fn: FunctionContext
    :return: function, a function to call to instantiate the function 
    """
    base_color = fn.input_parameter('diffuse_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    ambient_lighting_ = fn.input_parameter('ambient_lighting', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)

    res = ambient_lighting_ * base_color
    return res


def intersect_sphere(fn):
    """
    Intersects a sphere with a ray and returns the distance to the intersection point
    A miss is returned as a negative distance

    :param fn: The function context to create the function in
    :type fn: FunctionContext
    :return: function, a function to call to instantiate the function 
    """
    o = fn.input_parameter('ray_origin', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    d = fn.input_parameter('ray_direction', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    sO = fn.input_parameter('sphere_origin', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    sR = fn.input_parameter('sphere_radius', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT1)
    A = fn.dot(d, d)
    bb = d * ([2.0, 2.0, 2.0] * (o - sO))
    B = fn.dot(bb, [1.0, 1.0, 1.0])
    C = fn.dot(sO, sO) + fn.dot(o, o) - 2.0 * fn.dot(o, sO) - sR * sR
    D = B * B - 4.0 * A * C
    DD = fn.sqrt(D)
    t = -0.5 * (B + DD) / A
    hit = D > 0.0
    # Mask a miss as a distance of -1
    t = fn.if_else(hit, t, -1.0)
    return t


def render_sphere(fn):
    """
    Renders and lights a sphere

    :param fn: The function context to create the function in
    :type fn: FunctionContext
    :return: function, a function to call to instantiate the function 
    """
    # Inputs
    sO = fn.input_parameter('sphere_origin', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    sR = fn.input_parameter('sphere_radius', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT1)
    light_dir = fn.input_parameter('light_dir', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT3)
    light_col = fn.input_parameter('light_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    ambient_color = fn.input_parameter('ambient_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    bg_color = fn.input_parameter('background_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    tiling = fn.input_parameter('tiling', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT1)

    # Non-input variables
    pixel_pos = fn.variable('$pos', widget_type=sbsenum.WidgetEnum.SLIDER_FLOAT2)

    # Import functions
    fn_intersect_sphere = fn.import_local_function('intersect_sphere')
    fn_sphere_uv = fn.import_local_function('sphere_uv')
    fn_ambient_lighting = fn.import_local_function('ambient_lighting')
    fn_phong_lighting = fn.import_local_function('phong_lighting')

    # Constants
    specular_intensity_f = .3
    specular_intensity = [specular_intensity_f] * 4
    fill_alpha = [.0, .0, 0.0, 1.0]

    # Light setup
    light_dir = fn.normalize(light_dir)

    # Camera ray
    o = [0.0, 0.0, 0.0]
    d = fn.normalize(fn.expand(pixel_pos, 1.0) - [.5, .5, 0])

    # Intersect sphere
    t = fn_intersect_sphere(o, d, sO, sR)

    i_point = o + d * t
    i_normal = fn.normalize(i_point - sO)

    # Create uv and sample textures
    uv = fn_sphere_uv(i_normal, tiling)
    base_color = fn.create_color_sampler(uv, 0, sbsenum.FilteringEnum.BILINEAR)
    roughness = fn.create_gray_sampler(uv, 1, sbsenum.FilteringEnum.BILINEAR)

    camera_dir = [0.0, 0.0, 0.0] - d

    # Light sphere
    out_col = fn_phong_lighting(i_normal,
                                base_color,
                                specular_intensity,
                                roughness,
                                camera_dir,
                                light_dir) * light_col
    out_col = out_col + fn_ambient_lighting(base_color, ambient_color)

    # Set alpha to one
    out_col = out_col + fill_alpha

    # Mask out pixels missing the sphere
    hit_col = fn.if_else(t > 0.0, out_col, bg_color)
    # Connect the output node and layout the graph
    return hit_col


def raytracer_pixel_processor(fn):
    """
    Creates the raytracing pixel processor.

    :param fn: The function context to create the function in
    :type fn: FunctionContext
    :return: function, a function to call to instantiate the function 
    """
    rt = fn.import_local_function('render_sphere')

    # Input parameters
    sO = fn.variable('sphere_origin', widget_type=sbsenum.WidgetEnum.SLIDER_FLOAT3)
    sR = fn.variable('sphere_radius', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT1)
    light_dir = fn.variable('light_direction', widget_type=sbsenum.WidgetEnum.SLIDER_FLOAT3)
    light_color = fn.variable('light_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    ambient_color = fn.variable('ambient_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    background_color = fn.variable('background_color', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT4)
    tiling = fn.variable('tiling_scale', widget_type=sbsenum.WidgetEnum.COLOR_FLOAT1)

    # Create the raytracer
    rt_fun = rt(sO, sR, light_dir, light_color, ambient_color, background_color, tiling)
    return rt_fun


def main():
    parser = argparse.ArgumentParser('Raytracer Pixel Processor')
    demo_cmd.add_default_arguments(parser)
    args = parser.parse_args()
    atk_dir = demo_cmd.get_automation_toolkit_directory(args)
    samples_dir = demo_cmd.get_automation_toolkit_samples_directory(args)
    packages_dir = demo_cmd.get_automation_toolkit_packages_directories(args)

    # Use the python api to find the command line tools
    sbs_context = context.Context()
    sbs_context.setAutomationToolkitInstallPath(atk_dir)
    sbs_context.setDefaultPackagePath(packages_dir)

    output_path = os.path.join(samples_dir, 'raytracer')
    output_file = os.path.join(output_path, 'raytracer.sbs')
    # Make sure the output directory exist
    demos.ensure_directory_creation(output_path)

    # Create our target document
    doc = sbsgenerator.createSBSDocument(sbs_context,
                                         aFileAbsPath=output_file,
                                         aGraphIdentifier='Raytracer')

    # Create ambient lighting function
    ag.generate_function(ambient_lighting, doc, name='ambient_lighting')

    # Create phong lighting function
    ag.generate_function(phong_lighting, doc, name='phong_lighting')

    # Create sphere intersection function
    ag.generate_function(intersect_sphere, doc, name='intersect_sphere')

    # Create sphere uv function
    ag.generate_function(sphere_uv, doc, name='sphere_uv')

    # Create function for raytracing a sphere
    ag.generate_function(render_sphere, doc, name='render_sphere')

    graph = doc.getSBSGraph(aGraphIdentifier='Raytracer')

    # Add a bunch of input parameters to the root graph to drive parameters
    # in the raytracer
    graph.addInputParameter('sphere_radius', aWidget=sbsenum.WidgetEnum.SLIDER_FLOAT1, aDefaultValue=30.0)
    graph.addInputParameter('sphere_origin', aWidget=sbsenum.WidgetEnum.SLIDER_FLOAT3, aDefaultValue=[0.0, 0.0, 130.0])
    graph.addInputParameter('light_direction', aWidget=sbsenum.WidgetEnum.SLIDER_FLOAT3,
                            aDefaultValue=[1.0, -1.0, -1.0])
    graph.addInputParameter('light_color', aWidget=sbsenum.WidgetEnum.COLOR_FLOAT4, aDefaultValue=[1.0, 1.0, .7, 0])
    graph.addInputParameter('ambient_color', aWidget=sbsenum.WidgetEnum.COLOR_FLOAT4, aDefaultValue=[0.3, 0.3, .6, 0])
    graph.addInputParameter('background_color', aWidget=sbsenum.WidgetEnum.COLOR_FLOAT4,
                            aDefaultValue=[0.3, 0.3, .6, 1.0])
    graph.addInputParameter('tiling_scale', aWidget=sbsenum.WidgetEnum.SLIDER_FLOAT1, aDefaultValue=10.0)

    # Create a simple network with a pixel processor
    # and some inputs
    pp_node = create_base_network(graph, doc)
    pp = pp_node.getPixProcFunction()

    # Instantiate a sphere raytracer in the pixel processor
    ag.generate_function(raytracer_pixel_processor, doc, fn_node=pp)

    doc.writeDoc()


if __name__ == '__main__':
    main()
