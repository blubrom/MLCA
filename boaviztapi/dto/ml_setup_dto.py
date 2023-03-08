from pydantic import BaseModel
from typing import Optional, List
from boaviztapi.dto.component_dto import Cpu, Ram, Disk, PowerSupply, Gpu
from boaviztapi.dto.server_dto import ServerDTO

from boaviztapi.model.components.component import (
    ComponentGPU,
    ComponentCPU,
    ComponentRAM,
    ComponentSSD,
    ComponentHDD,
    ComponentPowerSupply,
    ComponentCase,
    Component
)
from boaviztapi.model.devices.device import Model, Server, CloudInstance
from boaviztapi.model.components.usage import UsageServer, UsageCloud
from boaviztapi.model.ml_setup import MLSetup

class MLSetupDTO(BaseModel):
  server: Optional[ServerDTO] = None
  gpu: Optional[Gpu] = None
  psf: Optional[float] = None
  train_time: Optional[float] = None

  def to_setup(self):
    setup = MLSetup()
    if self.server:
      setup.server = self.server.to_device()
    if self.gpu:
      setup.gpus = [ComponentGPU(**self.gpu.dict()) for _ in range(self.gpu.units)]
    setup.psf = self.psf
    setup.train_time_hours = self.train_time
    return setup