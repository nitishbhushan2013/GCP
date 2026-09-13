"""
Epic 6 / Phase B / B2 — Parse PDFs via Document AI (async batch).
"""

import re
from google.cloud import documentai_v1 as documentai
from google.cloud import storage

PROJECT_ID = "budgetsense-gcp-prod"
LOCATION = "us"  # per ADR-006 region exception
PROCESSOR_ID = "1bd3e26847822f34"

INPUT_BUCKET = "budgetsense-gcp-prod-docs"
INPUT_PREFIX = "source-documents/"
OUTPUT_BUCKET = "budgetsense-gcp-prod-docs"
OUTPUT_PREFIX = "docai-output/"

def _clear_output_prefix():
    """Delete any existing output blobs before a new batch run, so stale
    shards from previous runs never get merged with the current run's
    output."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(OUTPUT_BUCKET)
    blobs = list(bucket.list_blobs(prefix=OUTPUT_PREFIX))
    if blobs:
        print(f"Clearing {len(blobs)} stale output blob(s) from previous run(s)...")
        bucket.delete_blobs(blobs)


def batch_process_pdfs() -> dict[str, list[documentai.Document]]:
    """Submit all PDFs under INPUT_PREFIX to Document AI batch processing.
    Blocks until complete, then returns {source_filename: Document object}."""
    _clear_output_prefix()
    
    client = documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
    )
    processor_name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)

    input_config = documentai.BatchDocumentsInputConfig(
        gcs_prefix=documentai.GcsPrefix(
            gcs_uri_prefix=f"gs://{INPUT_BUCKET}/{INPUT_PREFIX}"
        )
    )
    output_config = documentai.DocumentOutputConfig(
        gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
            gcs_uri=f"gs://{OUTPUT_BUCKET}/{OUTPUT_PREFIX}"
        )
    )

    request = documentai.BatchProcessRequest(
        name=processor_name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    print("Submitting batch job...")
    operation = client.batch_process_documents(request)
    print(f"Waiting for operation to complete: {operation.operation.name}")
    operation.result(timeout=600)  # raises on failure, blocks until done

    return _read_batch_output()


def _read_batch_output() -> dict[str, list[documentai.Document]]:
    """Read the sharded JSON output Document AI wrote to GCS, keyed by
    original source filename. Returns a LIST of Document shards per file
    (in shard order) — large documents get split across multiple shards,
    each covering a page range with its own local text/text_anchor offsets."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(OUTPUT_BUCKET)

    shards_by_source: dict[str, list[tuple[int, documentai.Document]]] = {}

    for blob in bucket.list_blobs(prefix=OUTPUT_PREFIX):
        if not blob.name.endswith(".json"):
            continue

        match = re.search(r"([^/]+?)-(\d+)\.json$", blob.name)
        if not match:
            continue
        source_name, shard_index = match.group(1), int(match.group(2))

        doc = documentai.Document.from_json(
            blob.download_as_bytes(), ignore_unknown_fields=True
        )
        shards_by_source.setdefault(source_name, []).append((shard_index, doc))

    # Sort each file's shards numerically (not alphabetically — "-10" would
    # otherwise sort before "-2").
    return {
        name: [doc for _, doc in sorted(shards, key=lambda pair: pair[0])]
        for name, shards in shards_by_source.items()
    }


# parse_pdfs_batch.py
if __name__ == "__main__":
    extracted = batch_process_pdfs()
    for filename, shards in extracted.items():
        total_chars = sum(len(doc.text) for doc in shards)
        print(f"{filename}: {len(shards)} shard(s), {total_chars:,} characters extracted")