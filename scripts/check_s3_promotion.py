"""Read the current manifest from S3; network/auth errors must not bypass ordering."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from release_lib.constants import MANIFEST_NAMES_BY_CHANNEL
from release_lib.manifests import VERSION_LINE
from release_lib.promotion import promotion_allowed

parser = argparse.ArgumentParser()
parser.add_argument('--allow-same-version', action='store_true')
args = parser.parse_args()
channel = os.environ['RELEASE_CHANNEL']
version = os.environ['RELEASE_VERSION']
manifest = MANIFEST_NAMES_BY_CHANNEL[channel][1]
key = f"{os.environ['S3_PATH']}/{manifest}"
common = ['--endpoint-url', os.environ['S3_ENDPOINT']]
head = subprocess.run(['aws', 's3api', 'head-object', '--bucket', os.environ['S3_BUCKET'], '--key', key, *common], capture_output=True, text=True)
existing = None
if head.returncode:
    if '(404)' not in head.stderr and '(NoSuchKey)' not in head.stderr:
        raise RuntimeError('Cannot verify current S3 version: ' + head.stderr)
else:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / manifest
        subprocess.run(['aws', 's3', 'cp', f"s3://{os.environ['S3_BUCKET']}/{key}", str(path), *common], check=True)
        match = VERSION_LINE.search(path.read_text())
        if not match:
            raise RuntimeError('Existing manifest is missing its version')
        existing = match[1]
if not promotion_allowed(version, existing, allow_same=args.allow_same_version):
    raise RuntimeError(f'Refusing to overwrite {existing} with {version}')
print('Channel promotion ordering verified')
