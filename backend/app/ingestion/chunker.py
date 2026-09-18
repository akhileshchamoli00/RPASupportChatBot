"""
Structure-aware chunking module.
Groups document elements logically (sections, tables, procedures) without breaking step sequences.
"""

from app.core.logging_config import logger


def create_structure_aware_chunks(
    elements: list[dict],
    target_size: int = 3000,
    overlap: int = 200
) -> list[dict]:
    """
    Groups structured document elements into coherent chunks targeting target_size chars (~700-1000 tokens).
    Preserves heading boundaries, table structures, and procedural step sequences.
    """
    if not elements:
        return []

    chunks = []
    current_elements = []
    current_length = 0

    def flush_chunk(carry_overlap: bool = True):
        nonlocal current_elements, current_length
        if not current_elements:
            return

        combined_text = "\n\n".join(e["text"] for e in current_elements)
        first_elem = current_elements[0]
        last_elem = current_elements[-1]

        chunk_meta = {
            "text": combined_text,
            "section": first_elem.get("section", "General"),
            "title": first_elem.get("title", ""),
            "page": first_elem.get("page"),
            "sheet": first_elem.get("sheet"),
            "row_start": first_elem.get("row_start"),
            "row_end": last_elem.get("row_end"),
        }
        chunks.append(chunk_meta)

        # Retain modest overlap elements within the same sheet/section for context continuity
        if carry_overlap and overlap > 0:
            overlap_elements = []
            accumulated_overlap = 0
            for elem in reversed(current_elements):
                if accumulated_overlap + len(elem["text"]) <= overlap:
                    overlap_elements.insert(0, elem)
                    accumulated_overlap += len(elem["text"])
                else:
                    break

            current_elements = overlap_elements
            current_length = accumulated_overlap
        else:
            current_elements = []
            current_length = 0

    for elem in elements:
        elem_text = elem["text"]
        elem_len = len(elem_text)
        elem_sheet = elem.get("sheet")

        # Boundary Check: If sheet changes (Excel sheets should NEVER bleed across chunks),
        # flush the chunk immediately without carrying over overlap
        if current_elements and elem_sheet and current_elements[-1].get("sheet") != elem_sheet:
            flush_chunk(carry_overlap=False)

        # If a single element is larger than target_size, flush existing and add it as its own chunk
        if elem_len >= target_size:
            flush_chunk(carry_overlap=False)
            current_elements = [elem]
            current_length = elem_len
            flush_chunk(carry_overlap=False)
            continue

        # If adding this element exceeds target_size and we already have content, flush
        if current_length + elem_len > target_size and current_elements:
            flush_chunk(carry_overlap=True)

        current_elements.append(elem)
        current_length += elem_len

    # Flush any remaining elements
    flush_chunk(carry_overlap=False)

    logger.info(f"Generated {len(chunks)} structure-aware chunks from {len(elements)} document elements.")
    return chunks
