import re
from typing import List, Dict, Optional, Tuple

def extract_article_number(text: str) -> Optional[int]:
    """
    Extracts article numbers from text.
    
    Examples:
    - "Pasal 13" -> 13
    - "BAB II Pasal 5" -> 5
    - "Ayat (1) Pasal 20" -> 20
    """
    # Pattern to find "Pasal <number>"
    patterns = [
        r'Pasal\s+(\d+)',  # Article 13
        r'pasal\s+(\d+)',  # article 13 (lowercase)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    return None

def parse_query(query: str) -> Dict[str, any]:
    """
    Parses the query to identify specific entities (supports regulations AND calendar).
    
    Returns:
        Dict with keys:
        - 'doc_type': 'regulation', 'calendar', 'general'
        - 'article_numbers': List[int] - mentioned article numbers
        - 'months': List[str] - mentioned months (for calendar)
        - 'dates': List[str] - specific dates (for calendar)
        - 'query_type': str - 'specific_article', 'specific_date', 'comparison', 'general'
        - 'keywords': List[str] - important keywords
    """
    result = {
        'doc_type': 'general',
        'article_numbers': [],
        'months': [],
        'dates': [],
        'query_type': 'general',
        'keywords': []
    }
    
    # ===== REGULATION DETECTION =====
    # Extract article numbers
    article_pattern = r'[Pp]asal\s+(\d+)'
    matches = re.findall(article_pattern, query)
    if matches:
        result['article_numbers'] = [int(m) for m in matches]
        result['doc_type'] = 'peraturan'
        result['query_type'] = 'comparison' if len(matches) > 1 else 'specific_article'
        return result  # Early return, this is clearly a regulation query
    
    # ===== CALENDAR DETECTION =====
    # Search for months
    months_id = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    month_pattern = r'\b(' + '|'.join(months_id) + r')\b'
    month_matches = re.findall(month_pattern, query, re.IGNORECASE)
    if month_matches:
        result['months'] = month_matches
        result['doc_type'] = 'kalender'
        result['query_type'] = 'specific_date'
    
    # Search for specific dates (format: "12 Januari", "tanggal 15")
    date_pattern = r'(?:tanggal\s+)?(\d{1,2})(?:\s+(' + month_pattern + r'))?'
    date_matches = re.findall(date_pattern, query, re.IGNORECASE)
    if date_matches:
        # Filter out empty month matches if present, and combine day and month if both exist
        formatted_dates = []
        for day, month in date_matches:
            if day:
                if month:
                    formatted_dates.append(f"{day} {month}")
                else:
                    formatted_dates.append(day)
        result['dates'] = formatted_dates
        result['doc_type'] = 'kalender'
        result['query_type'] = 'specific_date'
    
    # Calendar keywords
    kalender_keywords = ['jadwal', 'acara', 'event', 'kegiatan', 'libur', 'ujian', 
                         'semester', 'kalender', 'kapan', 'tanggal']
    if any(kw in query.lower() for kw in kalender_keywords):
        if result['doc_type'] == 'general':  # If not yet detected
            result['doc_type'] = 'kalender'
    
    # ===== KEYWORD EXTRACTION =====
    stopwords = ['apa', 'yang', 'di', 'ke', 'dari', 'dan', 'atau', 'adalah', 
                 'sebutkan', 'jelaskan', 'dokumen', 'kapan', 'berapa', 'tentang']
    words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
    result['keywords'] = [w for w in words if w not in stopwords]
    
    return result

def merge_adjacent_chunks(chunks: List[any], max_chunks: int = 5) -> List[str]:
    """
    Merges adjacent chunks (from the same or consecutive pages).
    
    Args:
        chunks: List of Document objects with metadata
        max_chunks: Maximum number of chunks to merge
        
    Returns:
        List of merged text content
    """
    if not chunks:
        return []
    
    # Group chunks by source and page
    grouped = {}
    for chunk in chunks[:max_chunks]:
        source = chunk.metadata.get('source', 'unknown')
        page = chunk.metadata.get('page', 0)
        key = f"{source}_{page}"
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(chunk.page_content)
    
    # Merge chunks from same page
    merged = []
    for key in sorted(grouped.keys()):
        merged.append("\n".join(grouped[key]))
    
    return merged

def rerank_results(results: List[any], query_info: Dict[str, any]) -> List[any]:
    """
    Re-ranks results based on relevance to the query.
    
    Args:
        results: List of Document objects from similarity search
        query_info: Dict from parse_query()
        
    Returns:
        Re-ranked list of Document objects
    """
    scored_results = []
    
    for doc in results:
        score = 0.0
        content = doc.page_content.lower()
        
        # Boost if it contains the searched article
        if query_info['article_numbers']:
            for article_num in query_info['article_numbers']:
                if f'pasal {article_num}' in content or f'pasal  {article_num}' in content:
                    score += 100  # Large boost for exact match
                    
                # Check metadata
                if doc.metadata.get('article_number') == article_num:
                    score += 200  # Even larger boost for metadata match
        
        # Boost if it contains keywords
        for keyword in query_info['keywords']:
            if keyword in content:
                score += 5
        
        # Boost based on content length (longer might be more complete)
        score += len(content) / 1000.0
        
        scored_results.append((score, doc))
    
    # Sort by score descending
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    return [doc for score, doc in scored_results]

def get_context_window(chunks: List[any], target_chunk_idx: int, window_size: int = 1) -> str:
    """
    Retrieves the context window (chunks before and after) of the target chunk.
    
    Args:
        chunks: List of all chunks
        target_chunk_idx: Index of target chunk
        window_size: How many chunks before/after to retrieve
        
    Returns:
        Merged context string
    """
    start_idx = max(0, target_chunk_idx - window_size)
    end_idx = min(len(chunks), target_chunk_idx + window_size + 1)
    
    context_chunks = chunks[start_idx:end_idx]
    return "\n\n---\n\n".join([c.page_content for c in context_chunks])