import ollama
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Tuple, Optional
import json
from document_processor import ArcadiaDocumentProcessor
import config

class LocalRAGSystem:
    def __init__(self):
        self.ollama_client = ollama.Client(host=config.OLLAMA_BASE_URL)
        self.chroma_client = chromadb.PersistentClient(path=config.VECTORDB_PATH)
        self.collection = self._get_or_create_collection()
        self.doc_processor = ArcadiaDocumentProcessor()
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(name=config.COLLECTION_NAME)
        except:
            collection = self.chroma_client.create_collection(
                name=config.COLLECTION_NAME,
                metadata={"description": "Arcadia MBSE documents and models"}
            )
        return collection
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        response = self.ollama_client.embeddings(
            model=config.EMBEDDING_MODEL,
            prompt=text
        )
        return response['embedding']
    
    def add_documents(self, file_paths: List[str]) -> Dict:
        """Process and add documents to the vector database"""
        results = {"processed": 0, "chunks_added": 0, "errors": []}
        
        for file_path in file_paths:
            try:
                chunks = self.doc_processor.process_file(file_path)
                
                if chunks:
                    # Prepare data for ChromaDB
                    documents = [chunk['content'] for chunk in chunks]
                    metadatas = [chunk['metadata'] for chunk in chunks]
                    ids = [f"{file_path}_{i}" for i in range(len(chunks))]
                    
                    # Generate embeddings
                    embeddings = []
                    for doc in documents:
                        embedding = self.embed_text(doc)
                        embeddings.append(embedding)
                    
                    # Add to collection
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids,
                        embeddings=embeddings
                    )
                    
                    results["processed"] += 1
                    results["chunks_added"] += len(chunks)
                else:
                    results["errors"].append(f"No content extracted from {file_path}")
                    
            except Exception as e:
                results["errors"].append(f"Error processing {file_path}: {str(e)}")
        
        return results
    
    def search_similar(self, query: str, n_results: int = 5, context_filter: Optional[str] = None) -> List[Dict]:
        """Search for similar documents with optional context filtering"""
        query_embedding = self.embed_text(query)
        
        # Build where clause for context filtering
        where_clause = None
        if context_filter and context_filter in config.MBSE_CONTEXT_TYPES:
            # Get keywords for the context type
            phase_info = config.ARCADIA_PHASES.get(context_filter, {})
            keywords = phase_info.get('keywords', [])
            
            # Create a filter that looks for documents containing context-relevant keywords
            # This is a simplified approach - in practice you might want more sophisticated filtering
            where_clause = {"$or": [{"type": {"$eq": f"xml_{context_filter}"}}, 
                                  {"element_type": {"$eq": context_filter}}]}
        
        try:
            if where_clause:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_clause
                )
            else:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
        except:
            # Fall back to simple query if filtering fails
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
        
        similar_docs = []
        for i in range(len(results['documents'][0])):
            similar_docs.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return similar_docs
    
    def _detect_context_from_query(self, query: str) -> Optional[str]:
        """Detect MBSE context from query keywords"""
        query_lower = query.lower()
        
        for context_type, phase_info in config.ARCADIA_PHASES.items():
            keywords = phase_info.get('keywords', [])
            if any(keyword in query_lower for keyword in keywords):
                return context_type
        
        return None
    
    def _build_context_aware_prompt(self, query: str, context_docs: List[Dict], 
                                  context_type: Optional[str] = None, model: str = None) -> str:
        """Build a context-aware prompt for MBSE analysis"""
        if model is None:
            model = config.DEFAULT_MODEL
        
        # Prepare context from retrieved documents
        context = "\n\n".join([
            f"Source: {doc['metadata'].get('source', 'Unknown')}\n"
            f"Type: {doc['metadata'].get('type', 'Unknown')}\n"
            f"Content: {doc['content']}"
            for doc in context_docs
        ])
        
        # Get context-specific guidance
        context_guidance = ""
        if context_type and context_type in config.ARCADIA_PHASES:
            phase_info = config.ARCADIA_PHASES[context_type]
            context_guidance = f"""
Focus on {phase_info['name']} ({phase_info['description']}).
Pay special attention to: {', '.join(phase_info['keywords'])}
"""
        
        # Auto-detect context if not provided
        if not context_type:
            detected_context = self._detect_context_from_query(query)
            if detected_context:
                phase_info = config.ARCADIA_PHASES[detected_context]
                context_guidance = f"""
This appears to be a {phase_info['name']} question.
Consider: {', '.join(phase_info['keywords'])}
"""
        
        # Create comprehensive MBSE-focused prompt
        prompt = f"""You are an expert in Model-Based Systems Engineering (MBSE) using the Arcadia methodology in Capella. 

{context_guidance}

Available Context:
{context}

User Question: {query}

Instructions for your response:
1. Base your answer primarily on the provided context
2. If context is insufficient, clearly state this and provide general MBSE/Arcadia guidance
3. Structure your response according to Arcadia methodology principles
4. Include relevant traceability considerations when applicable
5. Mention verification/validation aspects if relevant
6. Use systems engineering terminology appropriately
7. Consider interfaces and interactions between system elements
8. Reference specific Arcadia phases and viewpoints when relevant

Provide a detailed, technical response that demonstrates deep understanding of both the specific content and MBSE best practices:"""

        return prompt
    
    def generate_response(self, query: str, context_docs: List[Dict], 
                         context_type: Optional[str] = None, model: str = None) -> str:
        """Generate context-aware response using Ollama"""
        if model is None:
            model = config.DEFAULT_MODEL
        
        prompt = self._build_context_aware_prompt(query, context_docs, context_type, model)
        
        try:
            response = self.ollama_client.generate(
                model=model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            )
            return response['response']
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def chat(self, query: str, n_context: int = 5, context_type: Optional[str] = None, 
            model: str = None) -> Tuple[str, List[Dict]]:
        """Main chat function with enhanced MBSE context awareness"""
        # Search for relevant context with optional filtering
        context_docs = self.search_similar(query, n_context, context_type)
        
        # Generate context-aware response
        response = self.generate_response(query, context_docs, context_type, model)
        
        return response, context_docs
    
    def get_collection_stats(self) -> Dict:
        """Get comprehensive statistics about the document collection"""
        count = self.collection.count()
        
        # Get type distribution
        try:
            all_metadata = self.collection.get()['metadatas']
            type_counts = {}
            for metadata in all_metadata:
                doc_type = metadata.get('type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        except:
            type_counts = {}
        
        return {
            "total_documents": count,
            "collection_name": config.COLLECTION_NAME,
            "type_distribution": type_counts,
            "supported_contexts": list(config.ARCADIA_PHASES.keys())
        }
    
    def get_model_recommendations(self, query: str) -> Dict:
        """Get model recommendations based on query type"""
        query_lower = query.lower()
        recommendations = {}
        
        for model, info in config.MODEL_RECOMMENDATIONS.items():
            score = 0
            for use_case in info['best_for']:
                if any(keyword in query_lower for keyword in use_case.lower().split()):
                    score += 1
            
            recommendations[model] = {
                "score": score,
                "info": info
            }
        
        # Sort by score
        sorted_recommendations = dict(sorted(recommendations.items(), 
                                           key=lambda x: x[1]['score'], reverse=True))
        
        return sorted_recommendations