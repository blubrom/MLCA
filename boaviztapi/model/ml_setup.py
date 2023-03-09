from abc import abstractmethod
from typing import List

from pydantic import BaseModel

from boaviztapi.model.devices.device import Model, Server
from boaviztapi.model.components.component import ComponentGPU
from boaviztapi.model.components.usage import UsageServer

# data from SNBC
_GWP_SNBC_KG = 2000
# data from Sala et al. (2020) "Environmental sustanability of European 
# production and consumption assessed against panetary boundaries"
# https://doi.org/10.1016/j.jenvman.2020.110686
_PB_CLIMATE_CHANGE_PER_CAPITA = 985
_PB_ADP_PER_CAPITA = 3.17E-02
_PB_WATER_USE_PER_CAPITA = 2.63E+04
_sig_PB = 3 

class MLSetup(BaseModel):
    server: Server = None
    gpus: List[ComponentGPU] = None
    psf: float = None
    model: Model = None
    train_time_hours: float = None
    
    # figures from Luccioni et al. (2022) 
    # "Estimating the carbon footprint of Bloom, a 176B parameter Language Model"
    # https://doi.org/10.48550/ARXIV.2211.02001
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
      # TODO: correct code at least to account for GPUs but also probably need corrections.
      impact_server,sig_server = self.server.impact_use_gwp()
      return self.psf * impact_server, sig_server
    
    
    def direct_impact_pe(self) -> (float, int):
      # TODO: correct code at least to account for GPUs but also probably need corrections.
      impact_server,sig_server = self.server.impact_use_pe()
      return self.psf * impact_server, sig_server
    
    
    def direct_impact_adp(self) -> (float, int):
      # TODO: correct code at least to account for GPUs but also probably need corrections.
      impact_server,sig_server = self.server.impact_use_adp()
      return self.psf * impact_server, sig_server
    
    
    def gwp_relative_SNBC(self) -> (float, int):
      embodied, sig_embodied = self.embodied_impact_gwp()
      direct, sig_direct = self.direct_impact_gwp()
      total_gwp = embodied + direct
      relative = total_gwp / _GWP_SNBC_KG
      return relative, min(sig_direct, sig_embodied)
    
    
    def gwp_relative_PB(self) -> (float, int):
      embodied, sig_embodied = self.embodied_impact_gwp()
      direct, sig_direct = self.direct_impact_gwp()
      total_gwp = embodied + direct
      relative = total_gwp / _PB_CLIMATE_CHANGE_PER_CAPITA
      return relative, min(sig_direct, sig_embodied, _sig_PB)
    
    
    def adp_relative_PB(self) -> (float, int):
      embodied, sig_embodied = self.embodied_impact_adp()
      direct, sig_direct = self.direct_impact_adp()
      total_gwp = embodied + direct
      relative = total_gwp / _PB_ADP_PER_CAPITA
      return relative, min(sig_direct, sig_embodied, _sig_PB)
    
    
    def smart_complete_data(self):
      if self.psf is None:
        self.psf = self._DEFAULT_PSF
      if self.train_time_hours is None:
        self.train_time_hours = self._DEFAULT_TIME
      if self.gpus is None:
        self.gpus = self.get_default_gpu()
      if self.server is None:
        self.server = self.get_default_server()
      
      for gpu in self.gpus:
        gpu.smart_complete_data()
      
      self.server.usage = UsageServer()
      self.server.smart_complete_data()
      # setup the use time accordingly to the specified training time
      self.server.usage.hours_use_time = self.train_time_hours
      # this parameter is reset to 0 since in the initialisation of UsageServer, it is assigned to 1 by default
      self.server.usage.years_use_time = 0
        
        
    def get_default_gpu(self) -> List[ComponentGPU]:
      return [ComponentGPU() for _ in range(self._DEFAULT_GPU_NUMBER)]
    
    
    def get_default_server(self) -> Server:
      return Server()