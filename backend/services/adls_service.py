from azure.storage.blob import BlobServiceClient
from backend.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER


def download_blob_stream(run_id: str, filename: str):
    """
    Download blob from ADLS as a streaming generator.
    Expected path on storage:
        {run_id}/{filename}
    """

    if not AZURE_STORAGE_CONNECTION_STRING:
        raise Exception("AZURE_STORAGE_CONNECTION_STRING not configured")

    blob_service = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )

    container = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)
    blob_path = f"{run_id}/{filename}"

    blob = container.get_blob_client(blob_path)
#
    print(" container_name",container)
    print("blobpath",blob_path)
    print("blob",blob)

    if not blob.exists():
        raise FileNotFoundError(f"Blob not found: {blob_path}")

    stream = blob.download_blob().chunks()
    return stream
