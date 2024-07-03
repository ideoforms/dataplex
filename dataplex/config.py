#--------------------------------------------------------------------------------
# Pydantic config definitions.
#--------------------------------------------------------------------------------

from typing import Optional, Union, Literal
from pydantic import BaseModel
import json

#--------------------------------------------------------------------------------
# Sources
#--------------------------------------------------------------------------------
class SourceConfig(BaseModel):
    type: str

class UltimeterSourceConfig(SourceConfig):
    type: Literal['ultimeter']
    port: Optional[str] = None
    interval: Optional[float] = None

class CSVSourceConfig(SourceConfig):
    type: Literal['csv']
    path: str
    rate: Optional[float] = 1.0

class JDPSourceConfig(SourceConfig):
    type: Literal['jdp']
    port: Optional[int] = 11000

class AudioSourceConfig(SourceConfig):
    type: Literal['audio']
    block_size: Optional[int] = 256

class VideoSourceConfig(SourceConfig):
    type: Literal['video']
    camera_index: Optional[int] = 2

#--------------------------------------------------------------------------------
# Destinations
#--------------------------------------------------------------------------------
class DestinationConfig(BaseModel):
    type: str

class OSCDestinationConfig(BaseModel):
    type: Literal['osc']
    host: str
    port: int

class JDPDestinationConfig(BaseModel):
    type: Literal['jdp']
    host: str
    port: int

class CSVDestinationConfig(BaseModel):
    type: Literal['csv']
    path: str

#--------------------------------------------------------------------------------
# Union types for sources and destinations
#--------------------------------------------------------------------------------

SourceUnion = Union[AudioSourceConfig,
                    VideoSourceConfig,
                    CSVSourceConfig,
                    JDPSourceConfig,
                    UltimeterSourceConfig]
DestinationUnion = Union[OSCDestinationConfig,
                         CSVDestinationConfig]

#--------------------------------------------------------------------------------
# Top-level config
#--------------------------------------------------------------------------------

class Config(BaseModel):
    sources: list[SourceUnion]
    destinations: list[DestinationUnion]

def load_config(config_path: str):
    return Config(**(json.load(open(config_path))))