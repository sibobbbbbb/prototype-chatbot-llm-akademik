"""
Enhanced ingestion with table extraction for calendar PDFs
"""
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from utils import extract_article_number
from table_extractor import CalendarTableExtractor, pdf_has_tables
import re

DOCS_DIR = "../documents"
DB_DIR = "../chroma_db"

def is_calendar_document(filename: str) -> bool:
    """Quick check if document is calendar"""
    return 'kalender' in filename.lower()

def is_peraturan_document(filename: str, content_sample: str) -> bool:
    """Quick check if document is peraturan"""
    has_peraturan = 'peraturan' in filename.lower()
    pasal_count = len(re.findall(r'Pasal\s+\d+', content_sample))
    return has_peraturan or pasal_count >= 3

def smart_split_by_articles(text: str, metadata: dict, max_chunk_size: int = 2000) -> list:
    """
    Split dokumen peraturan dengan prioritas pada batas pasal.
    """
    chunks = []
    pasal_pattern = r'(Pasal\s+\d+)'
    parts = re.split(pasal_pattern, text)
    
    current_chunk = ""
    current_article = None
    
    for i, part in enumerate(parts):
        if re.match(pasal_pattern, part.strip()):
            if current_chunk.strip():
                chunks.append({
                    'content': current_chunk.strip(),
                    'article_number': current_article,
                    'metadata': metadata.copy()
                })
            current_chunk = part
            current_article = extract_article_number(part)
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
                        'metadata': metadata.copy()
                    })
                current_chunk = sub_chunks[-1] if sub_chunks else ""
    
    if current_chunk.strip():
        chunks.append({
            'content': current_chunk.strip(),
            'article_number': current_article,
            'metadata': metadata.copy()
        })
    
    return chunks

def main():
    print(f"🚀 MEMULAI INGESTION DENGAN TABLE EXTRACTION...")
    
    if os.path.exists(DB_DIR):
        print("🧹 Menghapus database lama...")
        shutil.rmtree(DB_DIR)

    print("📄 Memuat dokumen PDF...")
    all_documents = []
    stats = {'peraturan': 0, 'kalender': 0, 'kalender_table': 0}
    
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".pdf"):
            print(f"\n   📝 Processing: {filename}")
            pdf_path = os.path.join(DOCS_DIR, filename)
            
            # DETECT DOCUMENT TYPE
            is_calendar = is_calendar_document(filename)
            
            if is_calendar:
                # CHECK IF IT HAS TABLES
                has_tables = pdf_has_tables(pdf_path, min_tables=1)
                
                if has_tables:
                    # USE TABLE EXTRACTION
                    print(f"   🔍 Detected: KALENDER with TABLES")
                    print(f"   📊 Using table extraction...")
                    
                    try:
                        chunks = CalendarTableExtractor.extract_from_pdf(pdf_path, filename)
                        
                        for chunk_data in chunks:
                            enriched_metadata = chunk_data['metadata']
                            enriched_metadata['extraction_method'] = 'table'
                            
                            all_documents.append(
                                Document(
                                    page_content=chunk_data['content'],
                                    metadata=enriched_metadata
                                )
                            )
                        
                        stats['kalender_table'] += len(chunks)
                        print(f"   ✓ Extracted {len(chunks)} chunks from tables")
                        continue  # Skip to next file
                        
                    except Exception as e:
                        print(f"   ⚠️  Table extraction failed: {e}")
                        print(f"   ↪️  Falling back to text extraction...")
            
            # FALLBACK OR NON-TABLE DOCUMENTS: Use PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            # Quick sample for detection
            sample_text = docs[0].page_content if docs else ""
            is_peraturan = is_peraturan_document(filename, sample_text)
            
            if is_peraturan:
                print(f"   🔍 Detected: PERATURAN (Article-based)")
            else:
                print(f"   🔍 Detected: GENERIC or TEXT-BASED CALENDAR")
            
            for doc in docs:
                base_metadata = {
                    "source": filename,
                    "page": doc.metadata.get("page", 0),
                    "extraction_method": "text"
                }
                
                # Choose extraction strategy
                if is_peraturan:
                    chunks = smart_split_by_articles(
                        doc.page_content,
                        base_metadata,
                        max_chunk_size=2000
                    )
                    doc_type = 'peraturan'
                else:
                    # Generic splitting for other documents
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=2000,
                        chunk_overlap=400
                    )
                    split_texts = splitter.split_text(doc.page_content)
                    chunks = [
                        {'content': text, 'metadata': base_metadata.copy()}
                        for text in split_texts
                    ]
                    doc_type = 'kalender' if is_calendar else 'generic'
                
                # Convert to Document objects
                for chunk_data in chunks:
                    enriched_metadata = chunk_data['metadata']
                    enriched_metadata['doc_type'] = doc_type
                    
                    if 'article_number' in chunk_data and chunk_data['article_number']:
                        enriched_metadata['article_number'] = chunk_data['article_number']
                        enriched_metadata['has_article'] = True
                    
                    all_documents.append(
                        Document(
                            page_content=chunk_data['content'],
                            metadata=enriched_metadata
                        )
                    )
                
                stats[doc_type] += len(chunks)
            
            print(f"   ✓ Generated {len(docs)} pages → chunks")
    
    print(f"\n✂️  Total {len(all_documents)} chunks dari semua dokumen.")
    print(f"\n📊 Statistik per tipe:")
    print(f"   - Peraturan (article-based): {stats['peraturan']} chunks")
    print(f"   - Kalender (table extraction): {stats['kalender_table']} chunks")
    print(f"   - Kalender/Generic (text): {stats['kalender']} chunks")

    print("\n🧠 Membuat Embedding & Menyimpan...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    Chroma.from_documents(documents=all_documents, embedding=embedding_model, persist_directory=DB_DIR)
    print("🎉 Database Siap dengan Table Extraction!")

if __name__ == "__main__":
    main()