import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_class_node(root, id, value, x, y, width=160, height=60, fill="#ffffff"):
    style = f"swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;fillColor={fill};"
    cell = ET.SubElement(root, "mxCell", id=id, value=value, style=style, vertex="1", parent="1")
    ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(width), height=str(height), as_="geometry")

def create_edge(root, id, source, target, edge_style, label=""):
    style = f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;{edge_style};"
    cell = ET.SubElement(root, "mxCell", id=id, value=label, style=style, edge="1", parent="1", source=source, target=target)
    ET.SubElement(cell, "mxGeometry", relative="1", as_="geometry")

mxfile = ET.Element("mxfile", version="20.3.0", type="device")
diagram = ET.SubElement(mxfile, "diagram", id="class_diagram", name="Earthquake OOP Architecture")
mxGraphModel = ET.SubElement(diagram, "mxGraphModel", dx="1600", dy="1200", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1600", pageHeight="1200", math="0", shadow="0")
root = ET.SubElement(mxGraphModel, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")

# --- Nodes ---
# Interfaces (Light Yellow)
if_color = "#fff2cc"
create_class_node(root, "IJob", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;BaseJob", 400, 50, fill=if_color)
create_class_node(root, "ISource", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;ISeismicDataSource", 100, 200, fill=if_color)
create_class_node(root, "IEnricher", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;IEnricher", 100, 400, fill=if_color)
create_class_node(root, "IStorage", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;ObjectStorage", 100, 600, fill=if_color)
create_class_node(root, "IEventRepo", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;IEventRepository", 100, 800, fill=if_color)
create_class_node(root, "IDQRepo", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;IDQRepository", 100, 950, fill=if_color)
create_class_node(root, "IDQCheck", "&lt;i&gt;&lt;&lt;Interface&gt;&gt;&lt;/i&gt;&lt;br&gt;IDQCheck", 700, 950, fill=if_color)

# Jobs (Light Blue)
job_color = "#dae8fc"
create_class_node(root, "BronzeJob", "BronzeIngestJob", 400, 200, fill=job_color)
create_class_node(root, "SilverJob", "SilverWriteJob", 400, 400, fill=job_color)
create_class_node(root, "LoadSilverJob", "LoadFromSilverJob", 400, 600, fill=job_color)
create_class_node(root, "BuildGoldJob", "BuildGoldJob", 400, 700, fill=job_color)
create_class_node(root, "LoadBIJob", "LoadBIToServingLayerJob", 400, 800, fill=job_color)
create_class_node(root, "DQJob", "DataQualityJob", 400, 950, fill=job_color)

# Implementations (Light Green)
impl_color = "#d5e8d4"
create_class_node(root, "USGSClient", "USGSClient", 100, 300, fill=impl_color)
create_class_node(root, "GeoEnricher", "GeoEnricher", -100, 500, fill=impl_color)
create_class_node(root, "RiskClass", "RiskClassifier", 100, 500, fill=impl_color)
create_class_node(root, "CompEnricher", "CompositeEnricher", 300, 500, fill=impl_color)
create_class_node(root, "S3Storage", "S3Storage", 100, 700, fill=impl_color)
create_class_node(root, "PgRepo", "PostgresRepository", 100, 1100, fill=impl_color)
create_class_node(root, "MagnitudeCheck", "MagnitudeSanityCheck", 700, 1100, fill=impl_color)
create_class_node(root, "OtherChecks", "...OtherChecks", 900, 1100, fill=impl_color)

# API Services (Light Red)
api_color = "#f8cecc"
create_class_node(root, "AuthSvc", "AuthService", 1200, 200, fill=api_color)
create_class_node(root, "TokenSvc", "TokenService", 1000, 350, fill=api_color)
create_class_node(root, "PwdSvc", "PasswordService", 1200, 350, fill=api_color)
create_class_node(root, "ApiEventRepo", "EventRepository", 1400, 200, fill=api_color)
create_class_node(root, "SavedEventRepo", "SavedEventRepository", 1400, 350, fill=api_color)
create_class_node(root, "AlertRuleRepo", "AlertRuleRepository", 1400, 450, fill=api_color)
create_class_node(root, "ApiRouter", "&lt;&lt;Facade&gt;&gt;&lt;br&gt;Auth Router", 1200, 50, fill="#e1d5e7")

# --- Edges ---
implements = "endArrow=block;dashed=1;endFill=0;"
inherits = "endArrow=block;endFill=0;"
aggregates = "endArrow=diamondThin;endFill=0;"
composes = "endArrow=diamondThin;endFill=1;"
depends = "endArrow=open;dashed=1;endFill=0;"

# Job Inheritance
create_edge(root, "e1", "BronzeJob", "IJob", inherits)
create_edge(root, "e2", "SilverJob", "IJob", inherits)
create_edge(root, "e3", "LoadSilverJob", "IJob", inherits)
create_edge(root, "e4", "BuildGoldJob", "IJob", inherits)
create_edge(root, "e5", "LoadBIJob", "IJob", inherits)
create_edge(root, "e6", "DQJob", "IJob", inherits)

# Interface Realization
create_edge(root, "e7", "USGSClient", "ISource", implements)
create_edge(root, "e8", "GeoEnricher", "IEnricher", implements)
create_edge(root, "e9", "RiskClass", "IEnricher", implements)
create_edge(root, "e10", "CompEnricher", "IEnricher", implements)
create_edge(root, "e11", "S3Storage", "IStorage", implements)
create_edge(root, "e12", "PgRepo", "IEventRepo", implements)
create_edge(root, "e13", "PgRepo", "IDQRepo", implements)
create_edge(root, "e14", "MagnitudeCheck", "IDQCheck", implements)
create_edge(root, "e15", "OtherChecks", "IDQCheck", implements)

# Dependencies / Associations
create_edge(root, "e16", "BronzeJob", "ISource", depends)
create_edge(root, "e17", "BronzeJob", "IStorage", depends)
create_edge(root, "e18", "SilverJob", "IEnricher", depends)
create_edge(root, "e19", "SilverJob", "IStorage", depends)
create_edge(root, "e20", "LoadSilverJob", "IStorage", depends)
create_edge(root, "e21", "LoadSilverJob", "IEventRepo", depends)
create_edge(root, "e22", "BuildGoldJob", "IEventRepo", depends)
create_edge(root, "e23", "BuildGoldJob", "IStorage", depends)
create_edge(root, "e24", "DQJob", "IDQRepo", depends)
create_edge(root, "e25", "DQJob", "IDQCheck", composes)
create_edge(root, "e26", "CompEnricher", "IEnricher", composes)

# API Layer
create_edge(root, "e27", "AuthSvc", "TokenSvc", composes)
create_edge(root, "e28", "AuthSvc", "PwdSvc", composes)
create_edge(root, "e29", "ApiRouter", "AuthSvc", depends)

xml_str = ET.tostring(mxfile, encoding="utf-8")
parsed = minidom.parseString(xml_str)
pretty_xml = parsed.toprettyxml(indent="  ")

with open("d:/projects/pp_earthquake/class_diagram.drawio", "w", encoding="utf-8") as f:
    f.write(pretty_xml)

print("Diagram generated successfully.")
