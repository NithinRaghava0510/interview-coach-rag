from app.services.document_parser import chunk_text


def test_chunk_text_overlaps_and_preserves_content():
    text = "Sentence one. " * 300
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) > 2
    assert all(chunks)
    assert max(map(len, chunks)) <= 320
