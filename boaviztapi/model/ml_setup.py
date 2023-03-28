from abc import abstractmethod
from typing import List

from pydantic import BaseModel

from boaviztapi.model.devices.device import Model, Server
from boaviztapi.model.components.component import ComponentGPU
from boaviztapi.model.components.usage import UsageComponent, UsageServer

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
    usage: UsageServer = None
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
        sum_impacts_manufacture = manufacture_server[0] + \
            sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min(
            [manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.train_time_hours * \
            self.embodied_impact_hour(sum_impacts_manufacture)
        return embodied, significant_figure_manufacture

    def embodied_impact_pe(self) -> (float, int):
        manufacture_gpu = [g.impact_pe() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_pe()
        sum_impacts_manufacture = manufacture_server[0] + \
            sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min(
            [manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.train_time_hours * \
            self.embodied_impact_hour(sum_impacts_manufacture)
        return embodied, significant_figure_manufacture

    def embodied_impact_adp(self) -> (float, int):
        manufacture_gpu = [g.impact_adp() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_adp()
        sum_impacts_manufacture = manufacture_server[0] + \
            sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min(
            [manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.train_time_hours * \
            self.embodied_impact_hour(sum_impacts_manufacture)
        return embodied, significant_figure_manufacture

    def dynamic_power(self) -> (float, int):
        # in Watts
        power_server = [item.power_draw()
                        for item in self.server.config_components]
        power_gpus = [item.power_draw() for item in self.gpus]
        significant_figures = min(p[1] for p in power_server + power_gpus)
        return (sum(p[0] for p in power_server + power_gpus)), significant_figures

    def energy_consumption(self) -> (float, int):
        # Wh
        # ratios taken from  Luccioni et al. (2022)
        # "Estimating the carbon footprint of Bloom, a 176B parameter Language Model"
        # https://doi.org/10.48550/ARXIV.2211.02001
        # table 2
        dynamic_power, sig = self.dynamic_power()
        dynamic_energy = dynamic_power * self.train_time_hours
        idle_energy = 64/109 * dynamic_energy
        infrastructure_energy = 27/109 * dynamic_energy
        return dynamic_energy + idle_energy + infrastructure_energy, min(3, sig)

    def direct_impact_gwp(self) -> (float, int):
        energy_consumption, sig = self.energy_consumption()
        return energy_consumption / 1000 * self.usage.impact_gwp, sig

    def direct_impact_pe(self) -> (float, int):
        energy_consumption, sig = self.energy_consumption()
        return energy_consumption / 1000 * self.usage.impact_pe, sig

    def direct_impact_adp(self) -> (float, int):
        energy_consumption, sig = self.energy_consumption()
        return energy_consumption / 1000 * self.usage.impact_adp, sig

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

        self.usage = UsageServer()
        self.usage.usage_location = self.usage_location
        self.usage.smart_complete_data()

    def get_default_gpu(self) -> List[ComponentGPU]:
        return [ComponentGPU() for _ in range(self._DEFAULT_GPU_NUMBER)]

    def get_default_server(self) -> Server:
        return Server()
