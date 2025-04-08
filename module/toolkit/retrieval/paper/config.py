# Local modules
from configs.config_cls import RetrievalConfig


PAPER_RETRIEVAL_CONFIG = RetrievalConfig(
    endpoint='http://127.0.0.1:8002',
    retrieve_api='/api/v1/query/search'
)