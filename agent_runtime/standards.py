"""V7.3 retrieval with versioned *authorized* references and explicit source trace.

Deterministic lexical retrieval is the safe baseline; pgvector or embeddings
may be added as an indexed accelerator without changing citation provenance.
No copyrighted TCVN/QCVN text is bundled or downloaded automatically.
"""
from __future__ import annotations
import hashlib
import re
from sqlalchemy import select
from .models import ReferenceDocument

WORDS = re.compile(r"[^\W_]{2,}", flags=re.UNICODE)


def terms(value: str) -> set[str]:
    return {s.casefold() for s in WORDS.findall(str(value)) if len(s) > 1}


def ingest_reference(db, *, project_id: str, source_id: str, version: str,
                     title: str, citation: str, text: str, copyright_permitted: bool,
                     effective_date: str = ""):
    if copyright_permitted is not True:
        raise PermissionError("Chỉ nhập tài liệu được phép sử dụng")
    if not (source_id and version and title and citation and text.strip()
            and len(text) <= 200_000 and len(citation) <= 300):
        raise ValueError("Tài liệu tiêu chuẩn/citation không hợp lệ")
    digest = hashlib.sha256(text.encode("utf8")).hexdigest()
    existing = db.scalar(select(ReferenceDocument).where(
        ReferenceDocument.project_id == project_id,
        ReferenceDocument.source_id == source_id,
        ReferenceDocument.source_version == version,
        ReferenceDocument.sha256 == digest))
    if existing:
        return existing
    doc = ReferenceDocument(
        project_id=project_id, source_id=source_id, source_version=version,
        title=title[:260], citation=citation, effective_date=effective_date[:30],
        text_excerpt=text, copyright_permitted=True, sha256=digest,
    )
    db.add(doc)
    db.flush()
    return doc


def query_refs(db, project_id: str, query: str, limit=5):
    requested = terms(query)
    if not requested:
        return []
    rows = db.scalars(select(ReferenceDocument).where(
        ReferenceDocument.project_id == project_id,
        ReferenceDocument.copyright_permitted.is_(True))).all()
    matches = []
    for row in rows:
        corpus = terms(row.title + " " + row.citation + " " + row.text_excerpt[:10000])
        overlap = len(requested & corpus)
        if not overlap:
            continue
        matches.append((overlap, row.id, {
            "title":row.title, "sourceId":row.source_id,
            "version":row.source_version, "citation":row.citation,
            "effectiveDate":row.effective_date, "sha256":row.sha256,
            # Bounded excerpt, not a proof of compliance or the full source.
            "excerpt":row.text_excerpt[:450], "matchTerms":overlap,
            "complianceVerified": False,
        }))
    return [m[2] for m in sorted(matches, key=lambda x:(-x[0], x[1]))[:limit]]
