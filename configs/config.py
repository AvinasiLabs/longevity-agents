import uuid
from pathlib import Path


# local module
from configs.config_cls import (
    SerpapiConfig, MinioConfig, IPFSConfig, MySQLConfig, EmbeddingConfig, OcrConfig
)


mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
MAC = "-".join([mac[e:e+2] for e in range(0, 11, 2)])

MACHINE_ID = 1


RELATIVE_PATH = Path(__file__).parent.parent
CACHE_DIR = RELATIVE_PATH.joinpath('.cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)


SERPAPI_CONFIG = SerpapiConfig(
    location='The University of Texas at Austin,Texas,United States',
    gl='us',
    hl='en'
)


MINIO_CONFIG = MinioConfig(
    host='127.0.0.1',
    port=9000,
    bucket='default',
    max_workers=32
)


IPFS_CONFIG = IPFSConfig(
    endpoint='http://127.0.0.1:8000',
    semaphore=32,
    timeout=300
)


MYSQL_CONFIG = MySQLConfig(
    charset='utf8mb4'
)


EMBEDDING_CONFIG = EmbeddingConfig(
    emb_type='openai',
    base_url='https://api.aimlapi.com/v1',
    timeout=1800,
    api='',
    semaphore=16,
    model="BAAI/bge-large-en-v1.5",
    batch_size=128
)


OCR_CONFIG = OcrConfig(
    base_url='http://127.0.0.1:48308/v1/ocr',
    timeout=3600,
    sema_process=4,
    ocr_cache=CACHE_DIR
)