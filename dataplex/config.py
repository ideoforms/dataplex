from typing import Optional, Union, Literal
from pydantic import BaseModel, TypeAdapter
import json

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

# Union types for sources and destinations
SourceUnion = Union[UltimeterSourceConfig, CSVSourceConfig]
DestinationUnion = Union[OSCDestinationConfig, CSVDestinationConfig]

class Config(BaseModel):
    sources: list[SourceUnion]
    destinations: list[DestinationUnion]

def load_config(config_path: str):
    return Config(**(json.load(open(config_path))))