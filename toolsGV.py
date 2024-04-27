import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pygraphviz as pgv
import re

def style_attrib_to_dict(style):
    d = {}
    for attrib in style.split(";"):
        attrib = attrib.split("=")
        try:
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
            edge["value"] = child.get("value")
            edge["source"] = child.get("source")
            edge["target"] = child.get("target")
            edge["style"] = style_attrib_to_dict(child.get("style"))
            edges.append(edge)
        else:
            vertice = {}
            vertice["id"] = child.get("id")
            vertice["value"] = child.get("value")
            vertice["style"] = style_attrib_to_dict(child.get("style"))
            vertice["style_no_dict"] = child.get("style")
            vertices.append(vertice)

def add_connections(graph, vertices, edges):
    for edge in edges:

        source = edge.get("source")
        target = edge.get("target")
        source_value = ""
        target_value = ""
        for vertice in vertices:
            if vertice["id"] == source:
                source_value = vertice['id']
            if vertice["id"] == target:
                target_value = vertice['id']
        if source_value != "" and target_value != "":
            graph.add_edge(source_value, target_value)     

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
