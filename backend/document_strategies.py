import re
from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentStrategy:
    """Base class for document processing strategy"""
    
    @staticmethod
    def detect(filename: str, content: str) -> bool:
        """Detect if the document matches this strategy"""
        raise NotImplementedError
    
    @staticmethod
    def chunk(text: str, metadata: dict, max_chunk_size: int = 2000) -> List[dict]:
        """Split the document according to the strategy"""
        raise NotImplementedError

class PeraturanStrategy(DocumentStrategy):
    """Strategy for regulatory documents (Articles)"""
    
    @staticmethod
    def detect(filename: str, content: str) -> bool:
        # Detect if there are many "Pasal" (Articles) in the document
        pasal_count = len(re.findall(r'Pasal\s+\d+', content))
        return pasal_count >= 3 or 'peraturan' in filename.lower()
    
    @staticmethod
    def chunk(text: str, metadata: dict, max_chunk_size: int = 2000) -> List[dict]:
        """Split based on articles (as already implemented)"""
        chunks = []
        pasal_pattern = r'(Pasal\s+\d+)'
        parts = re.split(pasal_pattern, text)
        
        current_chunk = ""
        current_article = None
        
        for part in parts:
            if re.match(pasal_pattern, part.strip()):
                if current_chunk.strip():
                    chunks.append({
                        'content': current_chunk.strip(),
                        'article_number': current_article,
                        'metadata': {**metadata, 'doc_type': 'peraturan'}
                    })
                current_chunk = part
                match = re.search(r'Pasal\s+(\d+)', part)
                current_article = int(match.group(1)) if match else None
            else:
                current_chunk += part
                if len(current_chunk) > max_chunk_size:
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=max_chunk_size,
                        chunk_overlap=200,
                        separators=["\n\n", "\n", ". ", " ", ""]
                    )
                    sub_chunks = splitter.split_text(current_chunk)
                    for sub_chunk in sub_chunks[:-1]:
                        chunks.append({
                            'content': sub_chunk,
                            'article_number': current_article,
                            'metadata': {**metadata, 'doc_type': 'peraturan'}
                        })
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
        
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'article_number': current_article,
                'metadata': {**metadata, 'doc_type': 'peraturan'}
            })
        
        return chunks

class KalenderStrategy(DocumentStrategy):
    """Strategy for academic calendars (Tables)"""
    
    @staticmethod
    def detect(filename: str, content: str) -> bool:
        # Detect if the word "kalender" (calendar) or many dates are present
        has_kalender = 'kalender' in filename.lower()
        # Count date patterns (e.g., "12 Januari 2024")
        date_count = len(re.findall(r'\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4}', content))
        return has_kalender or date_count >= 5
    
    @staticmethod
    def chunk(text: str, metadata: dict, max_chunk_size: int = 2000, pdf_path: str = None) -> List[dict]:
        """
        Split based on tables (if present) or months/events
        
        Args:
            text: Text content of the page
            metadata: Base metadata
            max_chunk_size: Max chunk size for text-based splitting
            pdf_path: Path to PDF for table extraction (optional)
        """
        chunks = []
        
        # STRATEGY 1: If a PDF path is provided and contains tables, use table extraction
        if pdf_path:
            try:
                from table_extractor import pdf_has_tables, CalendarTableExtractor
                
                if pdf_has_tables(pdf_path, min_tables=1):
                    # PDF has tables, use table extractor
                    # Note: this will extract the entire PDF, not per page
                    # We skip for now and fallback to text-based
                    pass  # Fallback to text-based below
            except Exception as e:
                print(f"   ⚠️  Table extraction error: {e}")
        
        # STRATEGY 2: Text-based splitting (fallback or default)
        # Split by month
        month_pattern = r'((?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+\d{4})'
        parts = re.split(month_pattern, text)
        
        current_chunk = ""
        current_month = None
        
        for i, part in enumerate(parts):
            month_match = re.match(month_pattern, part.strip())
            if month_match:
                if current_chunk.strip():
                    chunks.append({
                        'content': current_chunk.strip(),
                        'month': current_month,
                        'metadata': {**metadata, 'doc_type': 'kalender'}
                    })
                current_month = month_match.group(1)
                current_chunk = part
            else:
                current_chunk += part
                
                # If too long, split further
                if len(current_chunk) > max_chunk_size:
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=max_chunk_size,
                        chunk_overlap=200
                    )
                    sub_chunks = splitter.split_text(current_chunk)
                    for sub_chunk in sub_chunks[:-1]:
                        chunks.append({
                            'content': sub_chunk,
                            'month': current_month,
                            'metadata': {**metadata, 'doc_type': 'kalender'}
                        })
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
        
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'month': current_month,
                'metadata': {**metadata, 'doc_type': 'kalender'}
            })
        
        return chunks

class GenericStrategy(DocumentStrategy):
    """Default strategy for general documents"""
    
    @staticmethod
    def detect(filename: str, content: str) -> bool:
        # Fallback strategy, always true
        return True
    
    @staticmethod
    def chunk(text: str, metadata: dict, max_chunk_size: int = 2000) -> List[dict]:
        """Generic split using RecursiveCharacterTextSplitter"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=400,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks_text = splitter.split_text(text)
        chunks = []
        
        for chunk_text in chunks_text:
            chunks.append({
                'content': chunk_text,
                'metadata': {**metadata, 'doc_type': 'generic'}
            })
        
        return chunks

# Factory for selecting the appropriate strategy
class DocumentStrategyFactory:
    """Factory for selecting a strategy based on the document"""
    
    STRATEGIES = [
        PeraturanStrategy,
        KalenderStrategy,
        GenericStrategy  # Must be last (fallback)
    ]
    
    @classmethod
    def get_strategy(cls, filename: str, content: str) -> DocumentStrategy:
        """Select the most suitable strategy"""
        for strategy_class in cls.STRATEGIES:
            if strategy_class.detect(filename, content):
                return strategy_class
        return GenericStrategy  # Fallback
