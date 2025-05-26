"""
Diagram Generator for Lightweight Capella Diagrams
Supports generation of initial diagrams based on natural language descriptions and RAG system
"""

import graphviz
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re
from collections import defaultdict

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
    importance: float = 1.0  # Importance score for overview filtering

class DiagramStyle:
    """Styling configuration for diagrams"""
    COLORS = {
        "actor": "#E8F4F9",      # Light blue
        "activity": "#F9F3E8",   # Light orange
        "function": "#E8F9E9",   # Light green
        "component": "#F9E8E8",  # Light red
        "interface": "#F0E8F9",  # Light purple
        "requirement": "#F9F9E8" # Light yellow
    }
    
    FONTS = {
        "family": "Arial",
        "size": "12"
    }
    
    EDGE_STYLES = {
        "splines": "ortho",      # Orthogonal edges
        "nodesep": "0.5",        # Node separation
        "ranksep": "0.7"         # Rank separation
    }
    
    NODE_STYLES = {
        "style": "filled",
        "fontname": FONTS["family"],
        "fontsize": FONTS["size"],
        "margin": "0.3,0.1"
    }

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
    
    def generate_diagram(self, description: str, diagram_type: DiagramType, max_elements: int = 7) -> graphviz.Digraph:
        """Generate an overview diagram based on natural language description and RAG context"""
        # Create diagram using graphviz with enhanced styling
        dot = graphviz.Digraph(comment=diagram_type.value)
        self._apply_diagram_styles(dot)
        
        # Parse description and create elements using RAG system
        all_elements = self._parse_description(description, diagram_type)
        
        # Filter elements for overview
        overview_elements = self._filter_for_overview(all_elements, max_elements)
        
        # Create clusters for organization
        clusters = self._create_clusters(overview_elements)
        
        # Add clusters and elements to diagram
        for cluster_name, elements in clusters.items():
            with dot.subgraph(name=f"cluster_{cluster_name}") as c:
                c.attr(label=cluster_name, style="rounded", bgcolor="#FAFAFA")
                for element in elements:
                    self._add_node(c, element)
        
        # Add connections between elements
        self._add_connections(dot, overview_elements)
        
        return dot
    
    def _apply_diagram_styles(self, dot: graphviz.Digraph):
        """Apply enhanced styling to the diagram"""
        # Graph attributes
        dot.attr(rankdir="TB", splines=DiagramStyle.EDGE_STYLES["splines"])
        dot.attr(nodesep=DiagramStyle.EDGE_STYLES["nodesep"])
        dot.attr(ranksep=DiagramStyle.EDGE_STYLES["ranksep"])
        
        # Default node attributes
        dot.attr("node", **DiagramStyle.NODE_STYLES)
        
        # Edge attributes
        dot.attr("edge", color="#666666", penwidth="1.5", arrowsize="0.8")
    
    def _add_node(self, graph: graphviz.Digraph, element: DiagramElement):
        """Add a styled node to the graph"""
        label = f"{element.name}"
        if element.description:
            # Add description as tooltip
            tooltip = element.description[:100] + "..." if len(element.description) > 100 else element.description
        else:
            tooltip = element.name
            
        graph.node(element.id,
                  label,
                  shape=self._get_shape_for_type(element.type),
                  fillcolor=DiagramStyle.COLORS.get(element.type, "#FFFFFF"),
                  tooltip=tooltip)
    
    def _filter_for_overview(self, elements: List[DiagramElement], max_elements: int) -> List[DiagramElement]:
        """Filter elements to show only the most important ones for overview"""
        # Sort elements by importance
        sorted_elements = sorted(elements, key=lambda x: x.importance, reverse=True)
        
        # Take top N elements
        return sorted_elements[:max_elements]
    
    def _create_clusters(self, elements: List[DiagramElement]) -> Dict[str, List[DiagramElement]]:
        """Group elements into clusters based on their type"""
        clusters = defaultdict(list)
        for element in elements:
            clusters[element.type.capitalize()].append(element)
        return clusters
    
    def _add_connections(self, dot: graphviz.Digraph, elements: List[DiagramElement]):
        """Add styled connections between elements"""
        element_ids = {e.id for e in elements}
        for element in elements:
            for conn in element.connections:
                if conn in element_ids:  # Only add connection if both elements are visible
                    dot.edge(element.id, conn, "", constraint="true")
    
    def _calculate_importance(self, element: DiagramElement, context_docs: List[Dict[str, Any]]) -> float:
        """Calculate importance score for an element based on context"""
        importance = 1.0
        
        # Increase importance based on frequency in documents
        mentions = sum(1 for doc in context_docs if element.name.lower() in doc['content'].lower())
        importance += mentions * 0.2
        
        # Increase importance based on connections
        importance += len(element.connections) * 0.1
        
        # Increase importance if it has a description
        if element.description:
            importance += 0.3
            
        return importance

    def _extract_elements_from_text(self, text: str, element_type: str, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract elements of a specific type from text with improved parsing"""
        elements = []
        # Enhanced pattern to catch more complex names and descriptions
        pattern = r'(?:^|\n)([A-Z][a-zA-Z0-9\s]+?)(?:\s*:\s*([^\.]+))?(?:\.|$)'
        matches = re.finditer(pattern, text)
        
        for idx, match in enumerate(matches):
            name = match.group(1).strip()
            desc = match.group(2).strip() if match.group(2) else None
            
            # Create element
            element = DiagramElement(
                id=f"{element_type.lower()}_{idx}",
                name=name,
                type=element_type,
                description=desc
            )
            
            # Calculate importance
            element.importance = self._calculate_importance(element, context_docs)
            
            elements.append(element)
        
        return elements
    
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
    
    def _extract_operational_activities(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract operational activities from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "activity", context_docs))
        return elements
    
    def _extract_operational_context(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract operational context elements from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "actor", context_docs))
        return elements
    
    def _extract_system_activities(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract system activities from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "activity", context_docs))
        return elements
    
    def _extract_system_functions(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract system functions from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "function", context_docs))
        return elements
    
    def _extract_logical_components(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract logical components from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "component", context_docs))
        return elements
    
    def _extract_physical_components(self, context_docs: List[Dict[str, Any]]) -> List[DiagramElement]:
        """Extract physical components from context documents"""
        elements = []
        for doc in context_docs:
            elements.extend(self._extract_elements_from_text(doc['content'], "component", context_docs))
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