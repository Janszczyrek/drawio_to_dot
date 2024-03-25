import xml.etree.ElementTree as ET

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
            edge["source"] = child.get("source")
            edge["target"] = child.get("target")
            edge["style"] = style_attrib_to_dict(child.get("style"))
            edges.append(edge)
        else:
            vertice = {}
            vertice["id"] = child.get("id")
            vertice["value"] = child.get("value")
            vertice["style"] = style_attrib_to_dict(child.get("style"))
            vertices.append(vertice)
            
def print_connections(vertices, edges):
    print("digraph {")
    for egde in edges:
        source = egde.get("source")
        target = egde.get("target")
        source_value = ""
        target_value = ""
        for vertice in vertices:
            if vertice["id"] == source:
                source_value = vertice.get("value")
            if vertice["id"] == target:
                target_value = vertice.get("value")
        print(f"{source_value}->{target_value}")
    print("}")
edges = []
vertices = []
create_dics_form_xml("test1.drawio", vertices, edges)
# print(vertices)
# print(edges)
print_connections(vertices, edges)
