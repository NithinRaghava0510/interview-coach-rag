from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentChunk
from app.services.embeddings import embedding_service


def retrieve_context(db: Session, session_id, query: str, limit: int = 8) -> list[DocumentChunk]:
    query_embedding = embedding_service.embed([query])[0]
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.session_id == session_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def format_context(chunks: list[DocumentChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(f"[{chunk.source_type} #{chunk.chunk_index}] {chunk.content}")
    return "\n\n".join(blocks)


def evidence_from_chunks(chunks: list[DocumentChunk], max_items: int = 3) -> list[dict]:
    evidence = []
    for chunk in chunks[:max_items]:
        evidence.append(
            {
                "source": chunk.source_type,
                "chunk_index": chunk.chunk_index,
                "excerpt": chunk.content[:280] + ("..." if len(chunk.content) > 280 else ""),
            }
        )
    return evidence
