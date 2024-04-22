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

def arrow_translate(ArrowType, ArrowFill):
    txt = "normal"
    if ArrowFill == "0":
        txt = "o" + "normal"

    if ArrowType == None:
        return None
    return txt

def create_dics_form_xml(xml, vertices, edges):
    tree = ET.parse(xml)
    root = tree.getroot().find("diagram").find("mxGraphModel").find("root")

    for child in root[2:]:

        if "source" in child.attrib and "target" in child.attrib:
            edge = {}
            edge["source"] = child.get("source")
            edge["target"] = child.get("target")
            edge["arrowhead"] = arrow_translate(child.get("endArrow"),child.get("endFill"))
            edge["arrowtail"] = arrow_translate(child.get("startArrow"),child.get("startFill"))
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
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        extras = ""
        if edge["arrowhead"] is not None:
            extras = extras + f"arrowhead={edge['arrowhead']}"
            
        if edge["arrowtail"] is not None:
            extras = extras + f"arrowtail={edge['arrowtail']}"
        source_value = ""
        target_value = ""
        for vertice in vertices:
            if vertice["id"] == source:
                source_value = vertice.get("value")
            if vertice["id"] == target:
                target_value = vertice.get("value")
        print(f"{source_value}->{target_value} {extras}")
    print("}")
edges = []
vertices = []
create_dics_form_xml("test1.drawio", vertices, edges)
# print(vertices)
# print(edges)
print_connections(vertices, edges)
