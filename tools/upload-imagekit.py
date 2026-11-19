#!/usr/bin/env python3
"""Upload selected catalog covers to ImageKit and write a non-secret URL manifest."""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import certifi
import requests

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'research' / 'imagekit-manifest.json'
UPLOAD_URL = 'https://upload.imagekit.io/api/v1/files/upload'

def main() -> None:
    private_key = os.environ.get('IMAGEKIT_PRIVATE_KEY')
    endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT', 'https://ik.imagekit.io/bookshelf').rstrip('/')
    if not private_key:
        raise SystemExit('Set IMAGEKIT_PRIVATE_KEY in a local environment file. Never commit or send it in chat.')
    force = '--force' in sys.argv
    selected = {node.findtext('isbn', '').replace('-', '') for node in ET.parse(ROOT / 'books.xml').findall('./books/book')}
    source_records = json.loads((ROOT / 'research' / 'records.json').read_text())
    source_records += json.loads((ROOT / 'research' / 'user-additions-2026-11-17.json').read_text())
    records = {record['isbnNormalized']: record for record in source_records}
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    covers = manifest.get('covers', {})
    uploaded = 0
    for isbn in sorted(selected):
        if isbn in covers and not force:
            continue
        record = records[isbn]
        path = ROOT / record['coverPath']
        content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        try:
            response = requests.post(UPLOAD_URL, auth=(private_key, ''), data={'fileName': path.name, 'folder': '/covers', 'useUniqueFileName': 'false', 'overwriteFile': 'true'}, files={'file': (path.name, path.read_bytes(), content_type)}, timeout=60, verify=certifi.where())
            response.raise_for_status()
            result = response.json()
        except requests.HTTPError as error:
            raise SystemExit(f'ImageKit rejected {path.name}: HTTP {error.response.status_code} — {error.response.text}')
        except Exception as error:
            raise SystemExit(f'ImageKit rejected {path.name}: {error}')
        covers[isbn] = {'url': result['url'], 'fileId': result['fileId'], 'filePath': result['filePath']}
        manifest = {'endpoint': endpoint, 'folder': '/covers', 'covers': covers}
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        uploaded += 1
        print(f'Uploaded {uploaded}: {isbn} — {path.name}')
    print(f'Done. {uploaded} uploaded; {len(covers)} URLs in {MANIFEST.relative_to(ROOT)}.')


if __name__ == '__main__':
    main()
