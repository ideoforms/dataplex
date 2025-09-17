#--------------------------------------------------------------------------------
# Pydantic config definitions.
#--------------------------------------------------------------------------------

from typing import Optional, Union, Literal
from pydantic import BaseModel
import json
import yaml
import os

#--------------------------------------------------------------------------------
# Sources
#--------------------------------------------------------------------------------
class SourceConfig(BaseModel):
    name: Optional[str] = None
    type: str
    enabled: Optional[bool] = True
    properties: Optional[Union[list[str], list[dict]]] = []

class UltimeterSourceConfig(SourceConfig):
    type: Literal['ultimeter']
    port: Optional[str] = None
    interval: Optional[float] = None

class SerialSourceConfig(SourceConfig):
    type: Literal['serial']
    port_name: Optional[str] = None

class CSVSourceConfig(SourceConfig):
    type: Literal['csv']
    path: str
    rate: Optional[float] = 1.0

class JDPSourceConfig(SourceConfig):
    type: Literal['jdp']
    port: Optional[int] = 48000

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

class StdoutDestinationConfig(BaseModel):
    type: Literal['stdout']

class ScopeDestinationConfig(BaseModel):
    type: Literal['scope']

#--------------------------------------------------------------------------------
# Union types for sources and destinations
#--------------------------------------------------------------------------------

SourceUnion = Union[AudioSourceConfig,
                    VideoSourceConfig,
                    SerialSourceConfig,
                    CSVSourceConfig,
                    JDPSourceConfig,
                    UltimeterSourceConfig]

DestinationUnion = Union[OSCDestinationConfig,
                         CSVDestinationConfig,
                         JDPDestinationConfig,
                         StdoutDestinationConfig,
                         ScopeDestinationConfig]

#--------------------------------------------------------------------------------
# Top-level config
#--------------------------------------------------------------------------------

class GeneralConfig(BaseModel):
    read_interval: Optional[float] = 0.25

from pydantic import Field

class Config(BaseModel):
    config: GeneralConfig = GeneralConfig()
    sources: list[SourceUnion] = Field(default_factory=list, discriminator='type')
    destinations: list[DestinationUnion] = []

def load_config(config_path: str):
    if not os.path.exists(config_path):
        raise FileNotFoundError("Config file not found: %s" % config_path)
    if config_path.endswith(".json"):
        return Config(**(json.load(open(config_path))))
    elif config_path.endswith(".yaml") or config_path.endswith(".yml"):
        return Config(**(yaml.safe_load(open(config_path))))