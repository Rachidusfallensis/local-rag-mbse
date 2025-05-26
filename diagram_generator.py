"""
Diagram Generator for Lightweight Capella Diagrams
Supports generation of initial diagrams based on natural language descriptions
"""

import graphviz
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

class DiagramType(Enum):
    OAB = "Operational Activity Breakdown"
    OCB = "Operational Context Breakdown"
    SAB = "System Activity Breakdown"
    SFB = "System Function Breakdown"
    LAB = "Logical Architecture Breakdown"
    PAB = "Physical Architecture Breakdown"

@dataclass
class DiagramElement:
    id: str
    name: str
    type: str
    description: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)

class DiagramTemplate:
    def __init__(self, diagram_type: DiagramType):
        self.diagram_type = diagram_type
        self.elements: List[DiagramElement] = []
        self.connections: List[Tuple[str, str, str]] = []
        
    def add_element(self, element: DiagramElement):
        self.elements.append(element)
        
    def add_connection(self, from_id: str, to_id: str, label: str = ""):
        self.connections.append((from_id, to_id, label))

class CapellaDiagramGenerator:
    def __init__(self):
        self.templates = {
            DiagramType.OAB: self._create_oab_template,
            DiagramType.OCB: self._create_ocb_template,
            DiagramType.SAB: self._create_sab_template,
            DiagramType.SFB: self._create_sfb_template,
            DiagramType.LAB: self._create_lab_template,
            DiagramType.PAB: self._create_pab_template
        }
    
    def generate_diagram(self, description: str, diagram_type: DiagramType) -> graphviz.Digraph:
        """Generate a diagram based on natural language description"""
        # Create diagram using graphviz
        dot = graphviz.Digraph(comment=diagram_type.value)
        dot.attr(rankdir='TB')
        
        # Parse description and create elements
        elements = self._parse_description(description, diagram_type)
        
        # Apply template
        template = self.templates[diagram_type]()
        
        # Add elements to diagram
        for element in elements:
            dot.node(element.id, 
                    f"{element.name}\\n{element.type}",
                    shape=self._get_shape_for_type(element.type))
        
        # Add connections
        for conn in template.connections:
            dot.edge(conn[0], conn[1], conn[2])
        
        return dot
    
    def _parse_description(self, description: str, diagram_type: DiagramType) -> List[DiagramElement]:
        """Parse natural language description into diagram elements"""
        # TODO: Implement NLP parsing
        # For now, return template elements
        return self.templates[diagram_type]().elements
    
    def _get_shape_for_type(self, element_type: str) -> str:
        """Get appropriate shape for element type"""
        shapes = {
            "actor": "ellipse",
            "activity": "rectangle",
            "function": "rectangle",
            "component": "box3d",
            "interface": "diamond",
            "requirement": "note"
        }
        return shapes.get(element_type, "rectangle")
    
    def _create_oab_template(self) -> DiagramTemplate:
        """Create Operational Activity Breakdown template"""
        template = DiagramTemplate(DiagramType.OAB)
        template.add_element(DiagramElement("root", "Root Activity", "activity"))
        return template
    
    def _create_ocb_template(self) -> DiagramTemplate:
        """Create Operational Context Breakdown template"""
        template = DiagramTemplate(DiagramType.OCB)
        template.add_element(DiagramElement("system", "System", "actor"))
        return template
    
    def _create_sab_template(self) -> DiagramTemplate:
        """Create System Activity Breakdown template"""
        template = DiagramTemplate(DiagramType.SAB)
        template.add_element(DiagramElement("root", "System Activity", "activity"))
        return template
    
    def _create_sfb_template(self) -> DiagramTemplate:
        """Create System Function Breakdown template"""
        template = DiagramTemplate(DiagramType.SFB)
        template.add_element(DiagramElement("root", "System Function", "function"))
        return template
    
    def _create_lab_template(self) -> DiagramTemplate:
        """Create Logical Architecture Breakdown template"""
        template = DiagramTemplate(DiagramType.LAB)
        template.add_element(DiagramElement("root", "Logical Component", "component"))
        return template
    
    def _create_pab_template(self) -> DiagramTemplate:
        """Create Physical Architecture Breakdown template"""
        template = DiagramTemplate(DiagramType.PAB)
        template.add_element(DiagramElement("root", "Physical Component", "component"))
        return template

# Example usage:
# generator = CapellaDiagramGenerator()
# diagram = generator.generate_diagram("Create a system with two components", DiagramType.LAB)
# diagram.render("output", format="png", cleanup=True) 