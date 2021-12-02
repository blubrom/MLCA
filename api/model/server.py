import json
from pydantic import BaseModel
from typing import Optional, List


class ModelServer(BaseModel):
    manufacturer: Optional[str] = None 
    name: Optional[str] = None 
    type: Optional[str] = None
    year: Optional[str] = None


class PowerSupply(BaseModel):
    units: Optional[int] = None
    unit_weight: Optional[float] = None


class Disk(BaseModel):
    units: Optional[int] = None
    type: Optional[str] = None
    capacity: Optional[int] = None
    density: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None


class Ram(BaseModel):
    units: Optional[int] = None
    capacity: Optional[int] = None
    density: Optional[float] = None
    process: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None
    integrator: Optional[str] = None


class Cpu(BaseModel):
    units: Optional[int] = None
    core_units: Optional[int] = None
    die_size: Optional[float] = None
    die_size_per_core: Optional[float] = None
    process: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None
    family: Optional[str] = None


class ConfigurationServer(BaseModel):
    cpu: Optional[Cpu] = None
    ram: Optional[List[Ram]] = None
    disk: Optional[List[Disk]] = None
    power_supply: Optional[PowerSupply] = None


class Server(BaseModel):
    model: Optional[ModelServer] = None
    configuration: Optional[ConfigurationServer] = None

    add_method: Optional[str] = None
    add_date: Optional[str] = None
