"""
Diagram Generator for Lightweight Capella Diagrams
Supports generation of initial diagrams based on natural language descriptions and RAG system
"""

import graphviz
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re

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
    def __init__(self, rag_system=None):
        self.rag_system = rag_system
        self.templates = {
            DiagramType.OAB: self._create_oab_template,
            DiagramType.OCB: self._create_ocb_template,
            DiagramType.SAB: self._create_sab_template,
            DiagramType.SFB: self._create_sfb_template,
            DiagramType.LAB: self._create_lab_template,
            DiagramType.PAB: self._create_pab_template
        }
    
    def generate_diagram(self, description: str, diagram_type: DiagramType) -> graphviz.Digraph:
        """Generate a diagram based on natural language description and RAG context"""
        # Create diagram using graphviz
        dot = graphviz.Digraph(comment=diagram_type.value)
        dot.attr(rankdir='TB')
        
        # Parse description and create elements using RAG system
        elements = self._parse_description(description, diagram_type)
        
        # Add elements to diagram
        for element in elements:
            dot.node(element.id, 
                    f"{element.name}\\n{element.type}",
                    shape=self._get_shape_for_type(element.type))
        
        # Add connections
        for element in elements:
            for conn in element.connections:
                if conn in [e.id for e in elements]:
                    dot.edge(element.id, conn, "")
        
        return dot
    
    def _parse_description(self, description: str, diagram_type: DiagramType) -> List[DiagramElement]:
        """Parse natural language description into diagram elements using RAG system"""
        elements = []
        
        if self.rag_system:
            # Create a context-aware query based on diagram type
            query = self._create_rag_query(description, diagram_type)
            
            # Get relevant context from RAG system
            response, context_docs = self.rag_system.chat(query)
            
            # Extract elements based on diagram type
            if diagram_type == DiagramType.OAB:
                elements = self._extract_operational_activities(context_docs)
            elif diagram_type == DiagramType.OCB:
                elements = self._extract_operational_context(context_docs)
            elif diagram_type == DiagramType.SAB:
                elements = self._extract_system_activities(context_docs)
            elif diagram_type == DiagramType.SFB:
                elements = self._extract_system_functions(context_docs)
            elif diagram_type == DiagramType.LAB:
                elements = self._extract_logical_components(context_docs)
            elif diagram_type == DiagramType.PAB:
                elements = self._extract_physical_components(context_docs)
        
        # If no elements found, use template
        if not elements:
            template = self.templates[diagram_type]()
            elements = template.elements
        
        return elements
    
    def _create_rag_query(self, description: str, diagram_type: DiagramType) -> str:
        """Create a RAG query based on diagram type"""
        queries = {
            DiagramType.OAB: "Extract operational activities and their relationships from: ",
            DiagramType.OCB: "Identify system actors and their interactions from: ",
            DiagramType.SAB: "List system activities and their dependencies from: ",
            DiagramType.SFB: "Extract system functions and their hierarchy from: ",
            DiagramType.LAB: "Identify logical components and their interfaces from: ",
            DiagramType.PAB: "Extract physical components and their connections from: "
        }
        return queries[diagram_type] + description
    
    def _extract_elements_from_text(self, text: str, element_type: str) -> List[DiagramElement]:
        """Extract elements of a specific type from text"""
        elements = []
        # Use regex to find potential elements
        pattern = r'([A-Z][a-zA-Z\s]+)(?:\s*:\s*([^\.]+))?'
        matches = re.finditer(pattern, text)
        
        for idx, match in enumerate(matches):
            name = match.group(1).strip()
            desc = match.group(2).strip() if match.group(2) else None
            element_id = f"{element_type.lower()}_{idx}"
            elements.append(DiagramElement(
                id=element_id,
                name=name,
                type=element_type,
                description=desc
            ))
        
        return elements
    
    def _extract_operational_activities(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract operational activities from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "activity"))
        return elements
    
    def _extract_operational_context(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract operational context elements from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "actor"))
        return elements
    
    def _extract_system_activities(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract system activities from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "activity"))
        return elements
    
    def _extract_system_functions(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract system functions from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "function"))
        return elements
    
    def _extract_logical_components(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract logical components from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "component"))
        return elements
    
    def _extract_physical_components(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract physical components from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "component"))
        return elements
    
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