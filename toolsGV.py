import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pygraphviz as pgv
import re

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

def create_dics_form_xml(xml, vertices, edges):
    tree = ET.parse(xml)
    root = tree.getroot().find("diagram").find("mxGraphModel").find("root")

    for child in root[2:]:

        if "source" in child.attrib and "target" in child.attrib:
            edge = {}
            edge["id"] = child.get("id")
            edge["value"] = child.get("value")
            edge["source"] = child.get("source")
            edge["target"] = child.get("target")
            edge["style"] = style_attrib_to_dict(child.get("style"))
            edges.append(edge)
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
            vertices.append(vertice)

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
            if "arrowtail" in edge["style"].keys() and edge["style"]["arrowtail"] is not None:
                graph.get_edge(source_value, target_value).attr['arrowtail'] = edge["style"]["arrowtail"]
            print(edge["style"].keys())
            if "strokeColor" in edge["style"].keys() and edge["style"]["strokeColor"] is not None:
                graph.get_edge(source_value, target_value).attr['color'] = edge["style"]["strokeColor"]
            

            

def add_vertices(graph, vertices):
    for vertice in vertices:
        if "edgeLabel" in vertice["style_no_dict"]:
            continue

        name = vertice['id']
        graph.add_node(name)

        value = vertice.get("value")
        if value:
            soup = BeautifulSoup(value, 'html.parser')
            label = ''.join(soup.stripped_strings)
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

        for s in style_list:
            if s == 'fillColor':
                graph.get_node(name).attr[s.lower()] = style[s].lower()
                graph.get_node(name).attr["style"] = "filled"
            elif s == 'strokeColor':
                graph.get_node(name).attr["color"] = style[s].lower()
            else:
                graph.get_node(name).attr[s.lower()] = style[s].lower()
        

def diagram(drawio_file):
    edges = []
    vertices = []
    create_dics_form_xml(drawio_file, vertices, edges)

    graph = pgv.AGraph(strict=False, directed=True)

    add_vertices(graph, vertices)
    add_connections(graph, vertices, edges)

    print(graph)
    print("\n")

#diagram("test1.drawio")
#diagram("test2.drawio")
#diagram("test3.drawio")
#diagram("quest00_diagram_DragonStory.drawio")
#diagram("quest2023-13_DragonStory_gameplay_quest_DragonStory_world_DragonStory_20230225174947_IGG.drawio")
#diagram("test_label.drawio")
#diagram("shapes.drawio")
#diagram("testarrowtypes.drawio")
