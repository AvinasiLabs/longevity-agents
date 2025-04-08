import uuid


# local module
from configs.config_cls import SerpapiConfig


mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
MAC = "-".join([mac[e:e+2] for e in range(0, 11, 2)])


SERPAPI_CONFIG = SerpapiConfig(
    location='The University of Texas at Austin,Texas,United States',
    gl='us',
    hl='en'
)