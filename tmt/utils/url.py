"""
Url handling helpers.
"""

import tmt.log
import tmt.utils
from tmt.utils import Path
from werkzeug.http import parse_options_header


def download(url: str, destination: Path, *, logger: tmt.log.Logger) -> Path:
    logger.debug(f"Downloading '{url}'.")
    with tmt.utils.retry_session() as session:
        response = session.get(url, stream=True)
    response.raise_for_status()
    if destination.is_dir():
        file_name = None
        if "Content-Disposition" in response.headers:
            # Use werkzeug to parse the Content-Disposition header, which supports filename*
            _, options = parse_options_header(response.headers["Content-Disposition"])
            # Try filename* first (RFC 6266), then fallback to filename
            file_name = options.get("filename*") or options.get("filename")
        if not file_name:
            file_name = response.url.split("/")[-1]
    else:
        if destination.exists():
            raise tmt.utils.GeneralError(f"Destination file already exists: {destination}")
        file_name = destination.name
        destination = destination.parent
    assert isinstance(file_name, str)  # Narrow type
    download_file = destination / file_name
    with download_file.open(mode="wb") as f:
        for chunk in response.iter_content(chunk_size=None):
            f.write(chunk)
    return download_file
