import os
import json
import xml.etree.ElementTree as ET
from typing import List, Dict
import PyPDF2
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import config

class ArcadiaDocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def process_file(self, file_path: str) -> List[Dict]:
        """Process a file and return chunks with metadata"""
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.pdf':
            return self._process_pdf(file_path)
        elif extension == '.docx':
            return self._process_docx(file_path)
        elif extension == '.txt':
            return self._process_txt(file_path)
        elif extension == '.xml':
            return self._process_xml(file_path)
        elif extension == '.json':
            return self._process_json(file_path)
        elif extension == '.aird':
            return self._process_aird(file_path)
        elif extension == '.capella':
            return self._process_capella(file_path)
        else:
            return []
    
    def _detect_arcadia_phase(self, content: str, element_type: str = None) -> str:
        """Detect which Arcadia phase this content relates to"""
        content_lower = content.lower()
        
        # Check content against phase keywords
        for phase, phase_info in config.ARCADIA_PHASES.items():
            keywords = phase_info.get('keywords', [])
            if any(keyword in content_lower for keyword in keywords):
                return phase
        
        # Default classification based on element type
        if element_type:
            if 'requirement' in element_type.lower():
                return 'system'
            elif 'function' in element_type.lower():
                return 'logical'
            elif 'component' in element_type.lower():
                return 'physical'
            elif 'actor' in element_type.lower():
                return 'operational'
        
        return 'system'  # Default fallback
    
    def _process_pdf(self, file_path: str) -> List[Dict]:
        chunks = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        text_chunks = self.text_splitter.split_text(text)
        for i, chunk in enumerate(text_chunks):
            arcadia_phase = self._detect_arcadia_phase(chunk)
            chunks.append({
                'content': chunk,
                'metadata': {
                    'source': file_path,
                    'type': 'pdf',
                    'chunk_id': i,
                    'total_chunks': len(text_chunks),
                    'arcadia_phase': arcadia_phase
                }
            })
        return chunks
    
    def _process_docx(self, file_path: str) -> List[Dict]:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        text_chunks = self.text_splitter.split_text(text)
        chunks = []
        for i, chunk in enumerate(text_chunks):
            arcadia_phase = self._detect_arcadia_phase(chunk)
            chunks.append({
                'content': chunk,
                'metadata': {
                    'source': file_path,
                    'type': 'docx',
                    'chunk_id': i,
                    'total_chunks': len(text_chunks),
                    'arcadia_phase': arcadia_phase
                }
            })
        return chunks
    
    def _process_txt(self, file_path: str) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        text_chunks = self.text_splitter.split_text(text)
        chunks = []
        for i, chunk in enumerate(text_chunks):
            arcadia_phase = self._detect_arcadia_phase(chunk)
            chunks.append({
                'content': chunk,
                'metadata': {
                    'source': file_path,
                    'type': 'txt',
                    'chunk_id': i,
                    'total_chunks': len(text_chunks),
                    'arcadia_phase': arcadia_phase
                }
            })
        return chunks
    
    def _process_xml(self, file_path: str) -> List[Dict]:
        """Process XML files, particularly Capella exports"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse XML and extract meaningful content
        soup = BeautifulSoup(content, 'xml')
        
        # Extract different types of model elements
        chunks = []
        
        # Extract requirements
        requirements = soup.find_all(['requirement', 'Requirement', 'ownedRequirements'])
        for req in requirements:
            req_content = f"Requirement: {req.get('name', 'Unnamed')}\n"
            if req.get('description'):
                req_content += f"Description: {req.get('description')}\n"
            if req.text and req.text.strip():
                req_content += f"Details: {req.text.strip()}"
            
            arcadia_phase = self._detect_arcadia_phase(req_content, 'requirement')
            
            chunks.append({
                'content': req_content,
                'metadata': {
                    'source': file_path,
                    'type': 'xml_requirement',
                    'element_id': req.get('id', ''),
                    'element_type': 'requirement',
                    'element_name': req.get('name', 'Unnamed'),
                    'arcadia_phase': arcadia_phase
                }
            })
        
        # Extract functions and components
        functions = soup.find_all(['function', 'Function', 'component', 'Component', 
                                 'ownedFunctions', 'ownedComponents'])
        for func in functions:
            func_content = f"Function/Component: {func.get('name', 'Unnamed')}\n"
            if func.get('description'):
                func_content += f"Description: {func.get('description')}\n"
            if func.get('type'):
                func_content += f"Type: {func.get('type')}\n"
            
            element_type = 'function' if 'function' in func.name.lower() else 'component'
            arcadia_phase = self._detect_arcadia_phase(func_content, element_type)
            
            chunks.append({
                'content': func_content,
                'metadata': {
                    'source': file_path,
                    'type': f'xml_{element_type}',
                    'element_id': func.get('id', ''),
                    'element_type': element_type,
                    'element_name': func.get('name', 'Unnamed'),
                    'arcadia_phase': arcadia_phase
                }
            })
        
        # Extract actors and operational entities
        actors = soup.find_all(['actor', 'Actor', 'ownedActors', 'operationalActor'])
        for actor in actors:
            actor_content = f"Actor: {actor.get('name', 'Unnamed')}\n"
            if actor.get('description'):
                actor_content += f"Description: {actor.get('description')}\n"
            
            chunks.append({
                'content': actor_content,
                'metadata': {
                    'source': file_path,
                    'type': 'xml_actor',
                    'element_id': actor.get('id', ''),
                    'element_type': 'actor',
                    'element_name': actor.get('name', 'Unnamed'),
                    'arcadia_phase': 'operational'
                }
            })
        
        # Extract interfaces
        interfaces = soup.find_all(['interface', 'Interface', 'ownedInterfaces'])
        for interface in interfaces:
            interface_content = f"Interface: {interface.get('name', 'Unnamed')}\n"
            if interface.get('description'):
                interface_content += f"Description: {interface.get('description')}\n"
            
            arcadia_phase = self._detect_arcadia_phase(interface_content, 'interface')
            
            chunks.append({
                'content': interface_content,
                'metadata': {
                    'source': file_path,
                    'type': 'xml_interface',
                    'element_id': interface.get('id', ''),
                    'element_type': 'interface',
                    'element_name': interface.get('name', 'Unnamed'),
                    'arcadia_phase': arcadia_phase
                }
            })
        
        return chunks
    
    def _process_json(self, file_path: str) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Convert JSON structure to searchable text
        text = self._json_to_text(data)
        text_chunks = self.text_splitter.split_text(text)
        
        chunks = []
        for i, chunk in enumerate(text_chunks):
            arcadia_phase = self._detect_arcadia_phase(chunk)
            chunks.append({
                'content': chunk,
                'metadata': {
                    'source': file_path,
                    'type': 'json',
                    'chunk_id': i,
                    'total_chunks': len(text_chunks),
                    'arcadia_phase': arcadia_phase
                }
            })
        return chunks
    
    def _process_aird(self, file_path: str) -> List[Dict]:
        """Process Arcadia/Capella .aird files"""
        # AIRD files are typically zip archives containing XML
        import zipfile
        chunks = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('.xml'):
                        with zip_ref.open(file_info) as xml_file:
                            content = xml_file.read().decode('utf-8')
                            # Process similar to XML
                            soup = BeautifulSoup(content, 'xml')
                            
                            # Extract model elements with enhanced metadata
                            elements = soup.find_all(['ownedFunctions', 'ownedComponents', 
                                                    'ownedRequirements', 'ownedActors'])
                            for element in elements:
                                if element.get('name'):
                                    content_text = f"Model Element: {element.get('name')}\n"
                                    if element.get('description'):
                                        content_text += f"Description: {element.get('description')}\n"
                                    if element.get('summary'):
                                        content_text += f"Summary: {element.get('summary')}\n"
                                    
                                    element_type = element.name.replace('owned', '').lower()
                                    arcadia_phase = self._detect_arcadia_phase(content_text, element_type)
                                    
                                    chunks.append({
                                        'content': content_text,
                                        'metadata': {
                                            'source': file_path,
                                            'type': 'aird_element',
                                            'element_id': element.get('id', ''),
                                            'element_name': element.get('name', ''),
                                            'element_type': element_type,
                                            'inner_file': file_info.filename,
                                            'arcadia_phase': arcadia_phase
                                        }
                                    })
        except Exception as e:
            print(f"Error processing AIRD file {file_path}: {e}")
        
        return chunks
    
    def _process_capella(self, file_path: str) -> List[Dict]:
        """Process Capella project files (.capella)"""
        chunks = []
        
        try:
            # Capella files are often XML-based or archives
            # First try to process as direct XML
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                if content.strip().startswith('<?xml'):
                    # Process as XML
                    return self._process_xml_capella_content(content, file_path)
                else:
                    # Try as text file
                    arcadia_phase = self._detect_arcadia_phase(content)
                    text_chunks = self.text_splitter.split_text(content)
                    
                    for i, chunk in enumerate(text_chunks):
                        chunk_phase = self._detect_arcadia_phase(chunk)
                        chunks.append({
                            'content': chunk,
                            'metadata': {
                                'source': file_path,
                                'type': 'capella_text',
                                'chunk_id': i,
                                'total_chunks': len(text_chunks),
                                'arcadia_phase': chunk_phase
                            }
                        })
            except UnicodeDecodeError:
                # Try as binary archive
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith(('.xml', '.capella', '.aird')):
                            with zip_ref.open(file_info) as inner_file:
                                inner_content = inner_file.read().decode('utf-8')
                                inner_chunks = self._process_xml_capella_content(
                                    inner_content, f"{file_path}#{file_info.filename}")
                                chunks.extend(inner_chunks)
                                
        except Exception as e:
            print(f"Error processing Capella file {file_path}: {e}")
        
        return chunks
    
    def _process_xml_capella_content(self, content: str, source_path: str) -> List[Dict]:
        """Process XML content from Capella files"""
        chunks = []
        soup = BeautifulSoup(content, 'xml')
        
        # Extract Capella-specific elements
        capella_elements = [
            ('ownedFunctions', 'function'),
            ('ownedComponents', 'component'), 
            ('ownedRequirements', 'requirement'),
            ('ownedActors', 'actor'),
            ('ownedInterfaces', 'interface'),
            ('ownedCapabilities', 'capability'),
            ('ownedMissions', 'mission')
        ]
        
        for element_tag, element_type in capella_elements:
            elements = soup.find_all(element_tag)
            for element in elements:
                if element.get('name'):
                    content_text = f"Capella {element_type.title()}: {element.get('name')}\n"
                    if element.get('description'):
                        content_text += f"Description: {element.get('description')}\n"
                    if element.get('summary'):
                        content_text += f"Summary: {element.get('summary')}\n"
                    
                    # Extract additional Capella-specific attributes
                    if element.get('nature'):
                        content_text += f"Nature: {element.get('nature')}\n"
                    if element.get('kind'):
                        content_text += f"Kind: {element.get('kind')}\n"
                    
                    arcadia_phase = self._detect_arcadia_phase(content_text, element_type)
                    
                    chunks.append({
                        'content': content_text,
                        'metadata': {
                            'source': source_path,
                            'type': f'capella_{element_type}',
                            'element_id': element.get('id', ''),
                            'element_name': element.get('name', ''),
                            'element_type': element_type,
                            'arcadia_phase': arcadia_phase,
                            'capella_nature': element.get('nature', ''),
                            'capella_kind': element.get('kind', '')
                        }
                    })
        
        return chunks
    
    def _json_to_text(self, obj, prefix=""):
        """Convert JSON object to searchable text"""
        if isinstance(obj, dict):
            text_parts = []
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    text_parts.append(f"{prefix}{key}:")
                    text_parts.append(self._json_to_text(value, prefix + "  "))
                else:
                    text_parts.append(f"{prefix}{key}: {value}")
            return "\n".join(text_parts)
        elif isinstance(obj, list):
            text_parts = []
            for i, item in enumerate(obj):
                text_parts.append(f"{prefix}Item {i}:")
                text_parts.append(self._json_to_text(item, prefix + "  "))
            return "\n".join(text_parts)
        else:
            return str(obj)