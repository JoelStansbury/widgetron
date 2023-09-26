import os
from datetime import  datetime

from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED

ZERO_EPOCH_TUPLE = (1980, 1, 1, 12, 1, 0)
ZERO_EPOCH_TIMESTAMP = str(int(datetime(*ZERO_EPOCH_TUPLE).timestamp()))

def zipdir(path, zip_path):
    """
    derived from: https://fekir.info/post/reproducible-zip-archives/
    """
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zipf:
        entries = []
        for root, dirs, files in os.walk(path):
            for d in dirs:
                entries.append( os.path.relpath(os.path.join(root, d),path) + "/" )
            for f in files:
                entries.append( os.path.relpath(os.path.join(root, f),path) )
        entries.sort()
        for e in entries:
            info = ZipInfo(
                filename=e,
                date_time=ZERO_EPOCH_TUPLE
            )
            info.create_system = 3
            if e.endswith("/"):
                info.external_attr = 0o40755  << 16 | 0x010
                info.compress_type = ZIP_STORED
                info.CRC = 0 # unclear why necessary, maybe a bug?
                zipf.mkdir(info)
            else:
                info.external_attr = 0o100644 << 16
                info.compress_type = ZIP_DEFLATED
                with open(os.path.join(path, e), 'rb') as data:
                    zipf.writestr(info, data.read())

