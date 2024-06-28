import base64
from xml.dom import minidom
import xml.etree.ElementTree as ET
import zlib
from bs4 import BeautifulSoup
import pygraphviz as pgv
import re
import argparse
from PIL import Image
from urllib.parse import unquote

scale = 75

global_edges = { }
global_vertices = { }
args = None

shapes_dict = {
    "ellipse":"ellipse",
    "rhombus":"diamond",
    "trapezoid":"trapezium",
    "parallelogram":"parallelogram",
    "hexagon":"hexagon",
    "step":"cds",
    "process":"note", 
    "singleArrow":"rarrow"
}

arrow_dict = {
    "classic":"normal",
    "oval":"dot",
    "none":"none",
    "diamond":"diamond",
    "open":"open",
    "classicThin":"normal",
    "openThin":"open",
    "classicThin":"normal",
    "openAsync":"lopen",
    "block":"normal",
    "blockThin":"normal",
    "box":"box",
    "circlePlus":"odot",
    "ERmany":"oinv",
}

def shape_translator(drawio_shape,style):
    if "star" in drawio_shape:
        return "star"
    if "singleArrow" == drawio_shape:
        if "direction" in style:
            dir = style[style.find("direction=")+10:].split(";")[0]
            if dir == "west":
                return "larrow"
        if "rotation" in style:
            rot = style[style.find("rotation=")+9:].split(";")[0]
            if rot == "-180":
                return "larrow"
        return shapes_dict[drawio_shape]
    else:
        try:
            return shapes_dict[drawio_shape]
        except KeyError:
            return "box"

def arrowtype_translator(typeofarrow, filldata=None):
    arrowtype = "normal"
    if typeofarrow in arrow_dict.keys():
        arrowtype = arrow_dict[typeofarrow]

    if filldata is not None and filldata=="0":
        arrowtype = "o" + arrowtype
    return arrowtype
        
def divide(x):
    x = x.split("=")
    if len(x) == 1:
        x.append(x[0])
        x[0] = "styleid"
    return x
    

def style_attrib_to_dict(style):
    style = style[:-1]
    detaildict = dict(divide(x) for x in style.split(";"))
    d = {}
    d["shape"] = "box"
    if args.pin:
        d["fixedsize"] = "true"
    for attrib in style.split(";"):
        attrib = attrib.split("=")
        if attrib[0] == 'endArrow':
            if "endFill" in detaildict.keys():
                d["arrowhead"] = arrowtype_translator(attrib[1], detaildict["endFill"])
            else:
                d["arrowhead"] = arrowtype_translator(attrib[1])
        if attrib[0] == 'startArrow':
            if "startFill" in detaildict.keys():
                d["arrowtail"] = arrowtype_translator(attrib[1], detaildict["startFill"])
            else:
                d["arrowtail"] = arrowtype_translator(attrib[1])
        try:
            if attrib[0] in shapes_dict.keys():
                d["shape"] = shape_translator(attrib[0],style)
            elif attrib[0] == "shape":
                d[attrib[0]] = shape_translator(attrib[1],style)
            else:
                d[attrib[0]]=attrib[1]
        except IndexError:
            pass
        
    return d

def create_new_edges(child, vertices, edges):
    pointarray = child.find("mxGeometry").find("Array")
    tempverticename = child.get("source") + "-" + child.get("target")
    prevedge = child.get("source")
    helperid = 1
    if pointarray is not None:
        for point in pointarray:
            newedge = {}
            newedge["id"] = f"{tempverticename}_{helperid}"
            newedge["source"] = prevedge
            newedge["created"] = True
            newedge["style"] = { }
            newedge["style"]["arrowhead"] = "none"
            newedge["style"]["arrowtail"] = "none"
            newvertice = {}
            newvertice["id"] = f"{tempverticename}_node_{helperid}"
            newedge["target"] = newvertice["id"]
            newvertice["x"] = point.get("x")
            newvertice["y"] = point.get("y")
            newvertice["fixedsize"] = "yes"
            newvertice["label"] = ""
            newvertice["width"] = 0
            newvertice["height"] = 0
            newvertice["value"] = ""
            newvertice["style"] = style_attrib_to_dict(child.get("style"))
            newvertice["style_no_dict"] = child.get("style")
            prevedge = newvertice["id"]
            helperid += 1
            vertices.append(newvertice)
            edges.append(newedge)
    else:
        geometrychild = child.find("mxGeometry")
        if geometrychild is not None:
            pass
    return prevedge

def create_dics_form_xml(xml, vertices, edges):
    tree = None
    root = None
    if xml[-4:] == ".png":
        im = Image.open(xml)
        im.load()
        xml = unquote(im.info["mxfile"])
        tree = ET.fromstring(xml)
        root = tree
    else:
        tree = ET.parse(xml)
        root = tree.getroot()
    root = root.find("diagram").find("mxGraphModel").find("root")
    global global_edges
    global global_vertices
    for child in root[2:]:

        if "source" in child.attrib and "target" in child.attrib:
            edge = {}
            edge["id"] = child.get("id")
            edge["value"] = child.get("value")
            edge["source"] = child.get("source")
            edge["target"] = child.get("target")
            edge["style"] = style_attrib_to_dict(child.get("style"))
            if args.keep_arrows_pos:
                edge["source"] = create_new_edges(child, vertices, edges)
                    
            edges.append(edge)
            global_edges[child.get("id")] = edge
        elif "edgeLabel" in child.get("style"):
            next((edge for edge in edges if edge["id"] == child.get("parent")), None)
            if edge is not None:
                edge["label"] = child.get("value")
        else:
            vertice = {}
            vertice["id"] = child.get("id")
            vertice["value"] = child.get("value")
            vertice["style"] = style_attrib_to_dict(child.get("style"))
            vertice["style_no_dict"] = child.get("style")
            vertice["parent"] = child.get("parent")
            for geometrychild in child:
                vertice["x"] = geometrychild.get("x")
                vertice["y"] = geometrychild.get("y")
                vertice["height"] = geometrychild.get("height")
                vertice["width"] = geometrychild.get("width")
            vertices.append(vertice)
            global_vertices[child.get("id")] = vertice

def label_to_args(args,label):
    if label:
        soup = BeautifulSoup(label,"html.parser")
        args["label"] = ''.join(soup.stripped_strings)
        
        pattern = r'font color="([^"]*)"'
        match = re.search(pattern, label)
        if match:
            font_color = match.group(1)
            args["fontcolor"] = font_color
    

def add_connections(graph, vertices, edges):
    for edge in edges:

        source = edge.get("source")
        target = edge.get("target")
        edge_label = edge.get("label")
        source_value = ""
        target_value = ""
        args = {}
        label_to_args(args,edge_label)
        for vertice in vertices:
            if vertice["id"] == source:
                source_value = vertice['id']
            if vertice["id"] == target:
                target_value = vertice['id']
        if source_value != "" and target_value != "":
            graph.add_edge(source_value, target_value,**args)
            if "arrowhead" in edge["style"].keys() and edge["style"]["arrowhead"] is not None:
                graph.get_edge(source_value, target_value).attr['arrowhead'] = edge["style"]["arrowhead"]
            #else if:
             #   graph.get_edge(source_value, target_value).attr['arrowhead'] = "none"
            if "arrowtail" in edge["style"].keys() and edge["style"]["arrowtail"] is not None:
                graph.get_edge(source_value, target_value).attr['arrowtail'] = edge["style"]["arrowtail"]
           # else:
            #    graph.get_edge(source_value, target_value).attr['arrowtail'] = "none"
            if "strokeColor" in edge["style"].keys() and edge["style"]["strokeColor"] is not None:
                graph.get_edge(source_value, target_value).attr['color'] = edge["style"]["strokeColor"]
            
            
def add_vertices(graph, vertices):
    global global_vertices
    for vertice in vertices:
        if "edgeLabel" in vertice["style_no_dict"]:
            continue

        name = vertice['id']
        graph.add_node(name)

        value = vertice.get("value")
        if value:
            soup = BeautifulSoup(value, 'html.parser')
            #label = ''.join(soup.stripped_strings)
            label = word_wrap(list(soup.stripped_strings))
            print(list(soup.stripped_strings))
        else:
            label = ""
        graph.get_node(name).attr['label'] = label

        style = vertice.get("style")
        style_list = list(style.keys())
        
        pattern = r'font face="([^"]*)"'
        match = re.search(pattern, value)
        if match:
            font_value = match.group(1)
            graph.get_node(name).attr["fontname"] = font_value

        pattern = r'font-size: ([^"]*)px'
        match = re.search(pattern, value)
        if match:
            font_value = match.group(1)
            graph.get_node(name).attr["fontsize"] = font_value

        if vertice.get("x") is not None or vertice.get("y") is not None and args.pin:
            posx = 0
            posy = 0
            if vertice.get("x") is not None:
                posx = float(vertice.get("x"))
            if vertice.get("y") is not None:
                posy = float(vertice.get("y"))
            if vertice.get("height") and vertice.get("width"):
                posx = posx+float(vertice.get("width"))/2
                posy = posy+float(vertice.get("height"))/2
            if vertice.get("parent") is not None and "parent" in global_vertices:
                parentobj = global_vertices[vertice.get("parent")]
                if parentobj.get("x") is not None:
                    posx += float(parentobj.get("x"))
                if parentobj.get("y") is not None:
                    posy -= float(parentobj.get("y"))
            graph.get_node(name).attr["pos"] = str(posx / scale) + "," + str(-posy / scale) + "!"
            
        if vertice.get("height") and vertice.get("width") and args.pin:
            graph.get_node(name).attr["height"] = str(int(vertice.get("height"))/scale)
            graph.get_node(name).attr["width"] = str(int(vertice.get("width"))/scale)           
        for s in style_list:
            if s == 'fillColor':
                graph.get_node(name).attr[s.lower()] = style[s].lower()
                graph.get_node(name).attr["style"] = "filled"
            elif s == 'strokeColor':
                graph.get_node(name).attr["color"] = style[s].lower()
            else:
                graph.get_node(name).attr[s.lower()] = style[s].lower()
        if "fixedsize" in vertice:
            graph.get_node(name).attr["fixedsize"] = True
            graph.get_node(name).attr["width"] = 0
            graph.get_node(name).attr["height"] = 0    

def decompress_diagram(input: str, output: str) -> None:
    with open(input, 'r') as file:
        diagram_file = file.read()
    
    mxfile_header_match = re.search(r'<mxfile[^>]+>', diagram_file)
    mxfile_header = mxfile_header_match.group(0)
    
    diagram_match = re.search(r"(<diagram.*?>)([\s\S]*?)(</diagram>)", diagram_file)    
    opening_tag = diagram_match.group(1)
    compressed_data = diagram_match.group(2)
    closing_tag = diagram_match.group(3)
    
    decompressed_data = zlib.decompress(base64.b64decode(compressed_data), -15)
    decoded_diagram = unquote(decompressed_data.decode())
    
    full_content = f"{mxfile_header}{opening_tag}{decoded_diagram}{closing_tag}</mxfile>"

    dom = minidom.parseString(full_content)
    full_content = dom.toprettyxml(indent="    ")
    
    with open(output, 'w') as output_file:
        output_file.write(full_content)

def word_wrap(strings):
    phrases = list(strings)
    for i in range(0, len(phrases)):
        phrase = str(phrases[i])
        phrase = phrase.replace(';', '\n')
        index = phrase.find(' ', 31)
        if index != -1:
            phrase = phrase[:index] + '\n' + phrase[index + 1:]
        phrases[i] = phrase
    return ''.join(phrases)



def diagram(drawio_file):
    edges = []
    vertices = []
    create_dics_form_xml(drawio_file, vertices, edges)

    graph = pgv.AGraph(strict=False, directed=True)

    add_vertices(graph, vertices)
    add_connections(graph, vertices, edges)

    print(graph)
    print("\n")
    if args.output is not None:
       with open(args.output, 'w+') as dot_file:
           dot_file.write(graph.to_string())
    if args.output_image is not None:
        graph.layout(args.layout)
        graph.draw(args.output_image)

parser = argparse.ArgumentParser(
    prog="drawio_to_dot",
    description="script that converts a given drawio file into a DOT graph format and renders it as graphics."
)
parser.add_argument("-i","--input",action="store", help="input .drawio file", required=True)
parser.add_argument("-o","--output",action="store", help="output .dot file", default="out.dot")
parser.add_argument("--output-image",action="store", help="output image", required=False)
parser.add_argument("-l","--layout",action="store",
                    help="layout engine to be used when creating output image",
                    required=False, choices=["dot","neato","twopi","circo","fdp","nop"], default="dot")
parser.add_argument("-p", "--pin",action="store_true", help="keep nodes size and position given in .drawio file", required=False)
parser.add_argument("-k", "--keep_arrows_pos",action="store_true", help="try to replicate the edge trajectory as in .drawio file", required=False)
parser.add_argument("-d", "--decompress", action="store_true", help="decompress the input .drawio file before processing", required=False)
args = parser.parse_args()

if args.input is not None:
    if args.decompress:
        decompress_diagram(args.input, "decompressed_"+args.input)
        diagram("decompressed_"+args.input)
    else:
        diagram(args.input)

#diagram("test1.drawio")
#diagram("test2.drawio")
#diagram("test3.drawio")
#diagram("quest00_diagram_DragonStory.drawio")
#diagram("quest2023-13_DragonStory_gameplay_quest_DragonStory_world_DragonStory_20230225174947_IGG.drawio")
#diagram("test_label.drawio")
#diagram("shapes.drawio")
#diagram("testarrowtypes.drawio")
