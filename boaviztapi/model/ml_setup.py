from abc import abstractmethod
from typing import List

from pydantic import BaseModel

from boaviztapi.model.devices.device import Model, Server
from boaviztapi.model.components.component import ComponentGPU

class MLSetup(BaseModel):
    server: Server = None
    gpus: List[ComponentGPU] = None
    psf: float = None
    model: Model = None
    train_time_hours: int = None
    
    # figures from Luccioni et al. (2022) "Estimating the carbon footprint of Bloom, a 176B parameter Language Model"
    _AVERAGE_USAGE = .85
    _REPLACEMENT_RATE = 6
    _DEFAULT_GPU_NUMBER = 1
    _DEFAULT_PSF = 1
    _DEFAULT_TIME = 1
    
    def embodied_impact_hour(self, manufacture_impact) -> float:
      return manufacture_impact / (self._REPLACEMENT_RATE * 365 * 24 * self._AVERAGE_USAGE)
  
    def embodied_impact_gwp(self) -> (float, int):
        manufacture_gpu = [g.impact_gwp() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_gwp()
        sum_impacts_manufacture = manufacture_server[0] + sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min([manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.train_time_hours * self.embodied_impact_hour(sum_impacts_manufacture)
        return self.psf * embodied, significant_figure_manufacture
    
    def embodied_impact_pe(self) -> (float, int):
        manufacture_gpu = [g.impact_pe() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_pe()
        sum_impacts_manufacture = manufacture_server[0] + sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min([manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.train_time_hours * self.embodied_impact_hour(sum_impacts_manufacture)
        return self.psf * embodied, significant_figure_manufacture
    
    def embodied_impact_adp(self) -> (float, int):
        manufacture_gpu = [g.impact_adp() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_adp()
        sum_impacts_manufacture = manufacture_server[0] + sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min([manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.train_time_hours * self.embodied_impact_hour(sum_impacts_manufacture)
        return self.psf * embodied, significant_figure_manufacture
    
    
    def direct_impact_gwp(self) -> (float, int):
      return self.psf * 0, 0
    
    def direct_impact_pe(self) -> (float, int):
      return self.psf * 0, 0
    
    def direct_impact_adp(self) -> (float, int):
      return self.psf * 0, 0
    
    def smart_complete_data(self):
      if self.psf is None:
        self.psf = self._DEFAULT_PSF
      if self.train_time_hours is None:
        self.train_time_hours = self._DEFAULT_TIME
      if self.gpus is None:
        self.gpus = self.get_default_gpu()
      if self.server is None:
        self.server = self.get_default_server()
      
      self.server.smart_complete_data()
      for gpu in self.gpus:
        gpu.smart_complete_data()
        
    def get_default_gpu(self) -> List[ComponentGPU]:
      return [ComponentGPU() for _ in range(self._DEFAULT_GPU_NUMBER)]
    
    def get_default_server(self) -> Server:
      return Server()