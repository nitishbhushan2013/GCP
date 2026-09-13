"""
Epic 6 / Phase B / B1 — Read source PDFs from Cloud Storage.

Downloads each budget PDF from the bucket into memory (bytes), ready to
hand off to Document AI in B2. Run standalone to sanity-check bucket
access before wiring this into the full ingestion pipeline.
"""

from google.cloud import storage

BUCKET_NAME = "budgetsense-gcp-prod-docs"
SOURCE_FILES = [
    "source-documents/bp1_2026-27.pdf",
    "source-documents/bp2_2026-27.pdf",
    "source-documents/budget-overview-2026-27.pdf",
]


def read_pdfs_from_bucket(bucket_name: str, filenames: list[str]) -> dict[str, bytes]:
    """Download each named PDF from the bucket, return {filename: pdf_bytes}."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    pdfs = {}
    for filename in filenames:
        blob = bucket.blob(filename)
        if not blob.exists():
            raise FileNotFoundError(f"{filename} not found in gs://{bucket_name}")
        pdfs[filename] = blob.download_as_bytes()
        print(f"Read {filename}: {len(pdfs[filename]):,} bytes")

    return pdfs


if __name__ == "__main__":
    pdfs = read_pdfs_from_bucket(BUCKET_NAME, SOURCE_FILES)
    print(f"\nDone — {len(pdfs)} PDF(s) loaded into memory.")
