from pydantic import BaseModel
from typing import Optional, List
from boaviztapi.dto.component_dto import Gpu
from boaviztapi.dto.server_dto import ServerDTO

from boaviztapi.model.components.component import ComponentGPU
from boaviztapi.model.ml_setup import MLSetup
from boaviztapi.model.components.usage import UsageSetup


class MLSetupDTO(BaseModel):
    server: Optional[ServerDTO] = None
    gpu: Optional[Gpu] = None
    psf: Optional[float] = None
    usage: Optional[UsageSetup] = None
    gpu_usage_ratio: Optional[float] = None
    cpu_usage_ratio: Optional[float] = None

    _DEFAULT_USAGE_RATIO = 1

    def to_setup(self):
        setup = MLSetup()
        if self.server:
            setup.server = self.server.to_device()
        if self.gpu:
            setup.gpus = [ComponentGPU(**self.gpu.dict())
                          for _ in range(self.gpu.units)]
        setup.psf = self.psf
        setup.usage = self.get_usage()
        setup.gpu_usage = self.get_gpu_usage()
        setup.cpu_usage = self.get_cpu_usage()
        return setup

    def get_usage(self) -> UsageSetup:
        if self.usage is None:
            return UsageSetup()
        else:
            return self.usage

    def get_cpu_usage(self) -> float:
        if self.cpu_usage_ratio is None:
            return self._DEFAULT_USAGE_RATIO
        return self.cpu_usage_ratio

    def get_gpu_usage(self) -> float:
        if self.gpu_usage_ratio is None:
            return self._DEFAULT_USAGE_RATIO
        return self.gpu_usage_ratio
