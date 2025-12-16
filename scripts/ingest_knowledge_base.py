"""
Knowledge Base Ingestion Script

Run locally to:
1. Read PDFs and text files from knowledge base
2. Chunk text content
3. Generate embeddings using sentence-transformers (all-mpnet-base-v2, 768 dims)
4. Insert into PostgreSQL with pgvector

Usage:
    python scripts/ingest_knowledge_base.py --knowledge-path ./data/knowledge_base

Note: This script uses sentence-transformers which is too large for Vercel.
      Run locally before deployment. The model generates 768-dimensional embeddings
      to match Google's text-embedding-004 used in production.

Requirements:
    pip install sentence-transformers pypdf

Environment:
    DATABASE_URL - PostgreSQL connection string (from .env)
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from typing import List, Tuple
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.knowledge_embedding import KnowledgeEmbedding

# Optional PDF support
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pypdf not installed. PDF files will be skipped.")
    print("Install with: pip install pypdf")


class KnowledgeIngester:
    """Ingests knowledge base files into PostgreSQL with pgvector"""

    def __init__(
        self,
        database_url: str,
        embedding_model: str = "all-mpnet-base-v2",
        chunk_size: int = 300,
        chunk_overlap: int = 50
    ):
        """
        Initialize ingester

        Args:
            database_url: PostgreSQL connection string
            embedding_model: Sentence transformers model name
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.database_url = database_url
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}...")
        self.model = SentenceTransformer(embedding_model)
        print(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        # Initialize database connection
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        if not PDF_SUPPORT:
            print(f"Skipping PDF (pypdf not installed): {pdf_path.name}")
            return ""

        try:
            print(f"  Extracting text from PDF: {pdf_path.name}...")
            reader = PdfReader(pdf_path)
            text_parts = []

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text)
                except Exception as e:
                    print(f"    Warning: Could not extract page {page_num}: {e}")
                    continue

            full_text = "\n\n".join(text_parts)
            print(f"    Extracted {len(full_text):,} characters from {len(reader.pages)} pages")
            return full_text

        except Exception as e:
            print(f"    Error reading PDF {pdf_path.name}: {e}")
            return ""

    def load_text_file(self, file_path: Path) -> str:
        """Load text from file with encoding detection"""
        try:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    content = file_path.read_text(encoding=encoding)
                    print(f"  Loaded {len(content):,} characters from {file_path.name}")
                    return content
                except UnicodeDecodeError:
                    continue

            print(f"  Error: Could not decode {file_path.name} with any encoding")
            return ""

        except Exception as e:
            print(f"  Error reading {file_path.name}: {e}")
            return ""

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks
        """
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph is longer than chunk_size, split by sentences
            if len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                sentences = para.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if not sentence.endswith('.'):
                        sentence += '.'

                    if len(current_chunk) + len(sentence) + 2 > self.chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        # Add overlap
                        if self.chunk_overlap > 0:
                            words = current_chunk.split()
                            overlap_words = max(1, self.chunk_overlap // 10)
                            current_chunk = " ".join(words[-overlap_words:]) + " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        current_chunk = current_chunk + " " + sentence if current_chunk else sentence
            else:
                # Add paragraph to current chunk
                if len(current_chunk) + len(para) + 2 > self.chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())

                    # Add overlap
                    if self.chunk_overlap > 0:
                        words = current_chunk.split()
                        overlap_words = max(1, self.chunk_overlap // 10)
                        current_chunk = " ".join(words[-overlap_words:]) + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    current_chunk = current_chunk + "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Filter empty chunks
        return [chunk for chunk in chunks if chunk]

    def process_file(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """
        Process single file, return list of (content, source, index) tuples

        Args:
            file_path: Path to file

        Returns:
            List of tuples (chunk_content, source_filename, chunk_index)
        """
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif suffix in ['.txt', '.md']:
            text = self.load_text_file(file_path)
        else:
            print(f"  Skipping unsupported file: {file_path.name}")
            return []

        if not text:
            return []

        print(f"  Chunking text...")
        chunks = self.chunk_text(text)
        print(f"    Created {len(chunks)} chunks")

        return [(chunk, file_path.name, i) for i, chunk in enumerate(chunks)]

    def ingest(self, knowledge_path: Path, clear_existing: bool = False):
        """
        Ingest all files from knowledge path into database

        Args:
            knowledge_path: Path to knowledge base folder or file
            clear_existing: If True, delete existing embeddings first
        """
        print("\n" + "=" * 70)
        print("KNOWLEDGE BASE INGESTION")
        print("=" * 70 + "\n")

        # Collect files to process
        if knowledge_path.is_file():
            files = [knowledge_path]
        else:
            files = list(knowledge_path.rglob('*'))
            files = [f for f in files if f.is_file() and f.suffix.lower() in ['.pdf', '.txt', '.md']]

        if not files:
            print(f"❌ No supported files found in {knowledge_path}")
            return

        print(f"📂 Found {len(files)} file(s) to process:\n")
        for f in files:
            print(f"   - {f.name}")
        print()

        # Process all files
        print("📄 Processing files...\n")
        all_data = []
        for file_path in files:
            print(f"Processing: {file_path.name}")
            data = self.process_file(file_path)
            all_data.extend(data)
            print()

        if not all_data:
            print("❌ No content extracted from files")
            return

        print(f"✅ Total chunks to embed: {len(all_data)}\n")

        # Generate embeddings
        print("🔮 Generating embeddings (this may take a while)...")
        contents = [d[0] for d in all_data]
        embeddings = self.model.encode(contents, show_progress_bar=True, convert_to_numpy=True)
        print(f"✅ Generated {len(embeddings)} embeddings\n")

        # Insert into database
        print("💾 Inserting into database...")
        session = self.Session()

        try:
            if clear_existing:
                deleted = session.query(KnowledgeEmbedding).delete()
                session.commit()
                print(f"   Cleared {deleted} existing embeddings")

            # Insert in batches
            batch_size = 100
            total_inserted = 0

            for i in range(0, len(all_data), batch_size):
                batch_data = all_data[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]

                for (content, source, chunk_idx), embedding in zip(batch_data, batch_embeddings):
                    embedding_obj = KnowledgeEmbedding(
                        embedding_id=str(uuid.uuid4()),
                        content=content,
                        embedding=embedding.tolist(),
                        source_file=source,
                        chunk_index=chunk_idx,
                        meta_info={}
                    )
                    session.add(embedding_obj)

                session.commit()
                total_inserted += len(batch_data)
                print(f"   Inserted {total_inserted}/{len(all_data)} embeddings")

            print(f"\n✅ Successfully ingested {total_inserted} embeddings into database!")

        except Exception as e:
            session.rollback()
            print(f"\n❌ Error during insertion: {e}")
            raise

        finally:
            session.close()

        print("\n" + "=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ingest knowledge base into PostgreSQL with pgvector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Ingest from default location
    python scripts/ingest_knowledge_base.py

    # Ingest from custom path
    python scripts/ingest_knowledge_base.py --knowledge-path /path/to/docs

    # Clear existing and ingest fresh
    python scripts/ingest_knowledge_base.py --clear

    # Use different embedding model (must be 768 dimensions)
    python scripts/ingest_knowledge_base.py --model sentence-transformers/all-mpnet-base-v2
        """
    )

    parser.add_argument(
        "--knowledge-path",
        type=Path,
        default=Path("data/knowledge_base"),
        help="Path to knowledge base folder or file (default: data/knowledge_base)"
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing embeddings before ingesting"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="all-mpnet-base-v2",
        help="Sentence transformers model name (default: all-mpnet-base-v2, 768 dims)"
    )

    args = parser.parse_args()

    # Load environment
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ Error: DATABASE_URL not set in environment")
        print("   Create a .env file with: DATABASE_URL=postgresql://...")
        sys.exit(1)

    if not args.knowledge_path.exists():
        print(f"❌ Error: Knowledge base path does not exist: {args.knowledge_path}")
        sys.exit(1)

    # Create ingester and run
    ingester = KnowledgeIngester(
        database_url=database_url,
        embedding_model=args.model
    )

    ingester.ingest(args.knowledge_path, clear_existing=args.clear)


if __name__ == "__main__":
    main()
