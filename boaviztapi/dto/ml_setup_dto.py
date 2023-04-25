from pydantic import BaseModel
from typing import Optional, List
from boaviztapi.dto.component_dto import Gpu
from boaviztapi.dto.server_dto import ServerDTO

from boaviztapi.model.components.component import ComponentGPU
from boaviztapi.model.ml_setup import MLSetup
from boaviztapi.model.components.usage import UsageSetup


class MLSetupDTO(BaseModel):
    nb_nodes: Optional[int] = None
    server: Optional[ServerDTO] = None
    gpu: Optional[List[Gpu]] = None
    psf: Optional[float] = None
    usage: Optional[UsageSetup] = None
    gpu_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    average_usage: Optional[float] = None
    hardware_replacement_rate: Optional[float] = None

    _DEFAULT_USAGE_RATIO = 1
    _DEFAULT_NB_NODES = 1

    def to_setup(self):
        setup = MLSetup()
        if self.server:
            setup.server = self.server.to_device()
        if self.gpu:
            list_gpus = []
            for g in self.gpu:
                list_gpus += [ComponentGPU(**g.dict())
                          for _ in range(g.units)]
            setup.gpus = list_gpus
        setup.psf = self.psf
        setup.average_usage = self.average_usage
        setup.hardware_replacement_rate = self.hardware_replacement_rate
        setup.usage = self.get_usage()
        setup.gpu_usage = self.get_gpu_usage()
        setup.cpu_usage = self.get_cpu_usage()
        setup.nb_nodes = self.get_nb_nodes()
        return setup

    def get_usage(self) -> UsageSetup:
        if self.usage is None:
            return UsageSetup()
        else:
            return self.usage

    def get_cpu_usage(self) -> float:
        if self.cpu_usage is None:
            return self._DEFAULT_USAGE_RATIO
        return self.cpu_usage

    def get_gpu_usage(self) -> float:
        if self.gpu_usage is None:
            return self._DEFAULT_USAGE_RATIO
        return self.gpu_usage

    def get_nb_nodes(self) -> int:
        return self.nb_nodes or self._DEFAULT_NB_NODES
