import pdfplumber
import pandas as pd
import re
from typing import List, Dict, Tuple
from datetime import datetime

class CalendarTableExtractor:
    """Extract and structure calendar data from PDF tables"""
    
    @staticmethod
    def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
        """
        Extract all tables from PDF
        
        Returns:
            List of pandas DataFrames, one per table found
        """
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables from this page
                page_tables = page.extract_tables()
                
                if page_tables:
                    for table_idx, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            df['_source_page'] = page_num + 1
                            df['_table_index'] = table_idx
                            tables.append(df)
        
        return tables
    
    @staticmethod
    def extract_month_from_text(text: str) -> str:
        """Extract month name from text"""
        months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        
        if not text:
            return None
            
        for month in months:
            if month.lower() in text.lower():
                return month
        return None
    
    @staticmethod
    def extract_date_from_text(text: str) -> str:
        """Extract date pattern from text"""
        if not text:
            return None
        
        # Pattern: "12-15 January 2024" or "12 January 2024"
        date_patterns = [
            r'(\d{1,2})\s*-?\s*(\d{1,2})?\s*(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s*(\d{4})?',
            r'(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    @staticmethod
    def table_to_chunks(df: pd.DataFrame, source_filename: str) -> List[Dict]:
        """
        Convert table DataFrame to chunks for vector DB
        
        Each row becomes a chunk with structured information
        """
        chunks = []
        
        # Get column names (clean them up)
        columns = [str(col).strip() if col else f"col_{i}" for i, col in enumerate(df.columns)]
        
        for idx, row in df.iterrows():
            # Combine all row data into readable text
            row_texts = []
            row_metadata = {
                'source': source_filename,
                'page': row.get('_source_page', 0),
                'table_index': row.get('_table_index', 0),
                'doc_type': 'kalender',
                'dates_list': [],  # Internal list
                'months_list': []  # Internal list
            }
            
            for col_name, value in row.items():
                if col_name.startswith('_'):  # Skip internal metadata columns
                    continue
                
                value_str = str(value).strip() if value and str(value) != 'nan' else ''
                
                if value_str:
                    row_texts.append(f"{col_name}: {value_str}")
                    
                    # Extract metadata
                    month = CalendarTableExtractor.extract_month_from_text(value_str)
                    if month and month not in row_metadata['months_list']:
                        row_metadata['months_list'].append(month)
                    
                    date = CalendarTableExtractor.extract_date_from_text(value_str)
                    if date and date not in row_metadata['dates_list']:
                        row_metadata['dates_list'].append(date)
            
            # Create chunk content
            if row_texts:
                content = " | ".join(row_texts)
                
                # Enrich metadata - CONVERT LISTS TO STRINGS for Chroma compatibility
                if row_metadata['months_list']:
                    row_metadata['month'] = row_metadata['months_list'][0]  # Primary month
                    row_metadata['months'] = ", ".join(row_metadata['months_list'])  # All months as string
                if row_metadata['dates_list']:
                    row_metadata['date'] = row_metadata['dates_list'][0]  # Primary date
                    row_metadata['dates'] = ", ".join(row_metadata['dates_list'])  # All dates as string
                
                # Remove internal list fields
                del row_metadata['months_list']
                del row_metadata['dates_list']
                
                chunks.append({
                    'content': content,
                    'metadata': row_metadata
                })
        
        return chunks
    
    @staticmethod
    def extract_from_pdf(pdf_path: str, source_filename: str) -> List[Dict]:
        """
        Main method: Extract tables from PDF and convert to chunks
        
        Args:
            pdf_path: Path to PDF file
            source_filename: Filename to store in metadata
            
        Returns:
            List of chunk dictionaries ready for vector DB
        """
        all_chunks = []
        
        # Extract all tables
        tables = CalendarTableExtractor.extract_tables_from_pdf(pdf_path)
        
        print(f"   📊 Found {len(tables)} tables in {source_filename}")
        
        # Convert each table to chunks
        for table_df in tables:
            chunks = CalendarTableExtractor.table_to_chunks(table_df, source_filename)
            all_chunks.extend(chunks)
            print(f"      → Generated {len(chunks)} chunks from table")
        
        return all_chunks

# Helper function to detect if PDF contains tables
def pdf_has_tables(pdf_path: str, min_tables: int = 2) -> bool:
    """
    Quick check if PDF contains tables
    
    Args:
        pdf_path: Path to PDF file
        min_tables: Minimum number of tables to consider it a table document
        
    Returns:
        True if PDF has enough tables
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            table_count = 0
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    table_count += len(tables)
                    
                if table_count >= min_tables:
                    return True
            
            return table_count >= min_tables
    except Exception as e:
        print(f"   ⚠️  Error checking tables: {e}")
        return False
