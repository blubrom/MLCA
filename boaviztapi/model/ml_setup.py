from abc import abstractmethod
from typing import List, Tuple, Optional
import functools
import boaviztapi.utils.roundit as rd

from pydantic import BaseModel

from boaviztapi.model.devices.device import Model, Server
from boaviztapi.model.components.component import Component, ComponentGPU
from boaviztapi.model.components.usage import UsageSetup

# data from SNBC
_GWP_SNBC_KG = 2000
# data from Sala et al. (2020) "Environmental sustanability of European
# production and consumption assessed against panetary boundaries"
# https://doi.org/10.1016/j.jenvman.2020.110686
_PB_CLIMATE_CHANGE_PER_CAPITA = 985
_PB_ADP_PER_CAPITA = 3.17E-02
_PB_WATER_USE_PER_CAPITA = 2.63E+04

#_sig_PB = 3


class MLSetup(BaseModel):
    server: Server = None
    gpus: List[ComponentGPU] = None
    usage: UsageSetup = None
    psf: float = None
    model: Model = None
    cpu_usage: float = None
    gpu_usage: float = None
    # train_time_hours: float = None

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
        embodied = self.usage.get_duration_hours() * \
            self.embodied_impact_hour(sum_impacts_manufacture)
        return embodied, significant_figure_manufacture

    def embodied_impact_pe(self) -> (float, int):
        manufacture_gpu = [g.impact_pe() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_pe()
        sum_impacts_manufacture = manufacture_server[0] + \
            sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min(
            [manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.usage.get_duration_hours() * \
            self.embodied_impact_hour(sum_impacts_manufacture)
        return embodied, significant_figure_manufacture

    def embodied_impact_adp(self) -> (float, int):
        manufacture_gpu = [g.impact_adp() for g in self.gpus]
        manufacture_server = self.server.impact_manufacture_adp()
        sum_impacts_manufacture = manufacture_server[0] + \
            sum(item[0] for item in manufacture_gpu)
        significant_figure_manufacture = min(
            [manufacture_server[1]] + [item[1] for item in manufacture_gpu])
        embodied = self.usage.get_duration_hours() * \
            self.embodied_impact_hour(sum_impacts_manufacture)
        return embodied, significant_figure_manufacture

    def dynamic_power(self) -> (float, int):
        def separate_cpu(acc: Tuple[float, float, float], item: Component) -> Tuple[float, float, float]:
            others, cpus, curr_s = acc
            p, s = item.power_draw()
            new_s = min(curr_s, s)
            if item.TYPE == 'CPU':
                return (others, cpus + p, new_s)
            return (others + p, cpus, new_s)

        def get_power_sig(acc, g):
            p, s = g.power_draw()
            return (acc[0] + p, min(acc[1], s))
        # following modelisation from the green algorithms tool, available at https://github.com/GreenAlgorithms/green-algorithms-tool
        # under https://creativecommons.org/licenses/by/4.0/ licence.
        # Lannelongue, L., Grealey, J., Inouye, M., Green Algorithms: Quantifying the Carbon Footprint of Computation.
        # Adv. Sci. 2021, 8, 2100707. https://doi.org/10.1002/advs.202100707
        # in kWatts
        # default sig put to 5 because it is higher than what is observed on the rest of the code
        power_server, power_cpus, sig_serv = functools.reduce(
            separate_cpu, self.server.config_components, (0, 0, 5))
        power_gpus, sig_gpu = functools.reduce(
            get_power_sig, self.gpus, (0, 5))
        return (self.cpu_usage * power_cpus + self.gpu_usage * power_gpus + power_server)/1000, min(sig_serv, sig_gpu)

    def energy_consumption(self) -> (float, int):
        # kWh
        # ratios taken from  Luccioni et al. (2022)
        # "Estimating the carbon footprint of Bloom, a 176B parameter Language Model"
        # https://doi.org/10.48550/ARXIV.2211.02001
        # table 2
        dynamic_power, sig = self.dynamic_power()
        dynamic_energy = dynamic_power * self.usage.get_duration_hours()
        ratio = 12
        # comes from the paper for Bloom being erroneous
        # idle_energy = 64/109 * dynamic_energy
        # infrastructure_energy = 27/109 * dynamic_energy
        return (dynamic_energy * ratio), sig

    def direct_impact_gwp(self) -> (float, int):
        return self.usage.impact_gwp()
        # energy_consumption, sig = self.energy_consumption()
        # return energy_consumption * self.usage.impact_gwp, sig

    def direct_impact_pe(self) -> (float, int):
        return self.usage.impact_pe()
        # energy_consumption, sig = self.energy_consumption()
        # return energy_consumption * self.usage.impact_pe, sig

    def direct_impact_adp(self) -> (float, int):
        return self.usage.impact_adp()
        # energy_consumption, sig = self.energy_consumption()
        # return energy_consumption * self.usage.impact_adp, sig

    def gwp_relative_SNBC(self) -> (float, int):
        embodied, sig_embodied = self.embodied_impact_gwp()
        direct, sig_direct = self.direct_impact_gwp()
        total_gwp = embodied + direct
        relative = total_gwp / _GWP_SNBC_KG
        sig = rd.significant_number(_GWP_SNBC_KG)
        return relative, min(sig_direct, sig_embodied, sig)

    def gwp_relative_PB(self) -> (float, int):
        embodied, sig_embodied = self.embodied_impact_gwp()
        direct, sig_direct = self.direct_impact_gwp()
        total_gwp = embodied + direct
        relative = total_gwp / _PB_CLIMATE_CHANGE_PER_CAPITA
        sig = rd.significant_number(_PB_CLIMATE_CHANGE_PER_CAPITA)
        return relative, min(sig_direct, sig_embodied, sig)

    def adp_relative_PB(self) -> (float, int):
        embodied, sig_embodied = self.embodied_impact_adp()
        direct, sig_direct = self.direct_impact_adp()
        total_gwp = embodied + direct
        relative = total_gwp / _PB_ADP_PER_CAPITA
        sig = rd.significant_number(_PB_ADP_PER_CAPITA)
        return relative, min(sig_direct, sig_embodied, sig)

    def smart_complete_data(self):
        if self.psf is None:
            self.psf = self._DEFAULT_PSF
        if self.gpus is None:
            self.gpus = self.get_default_gpu()
        if self.server is None:
            self.server = self.get_default_server()
        if self.gpu_usage is None:
            self.gpu_usage = self._DEFAULT_USAGE_RATE
        if self.cpu_usage is None:
            self.cpu_usage = self._DEFAULT_USAGE_RATE

        for gpu in self.gpus:
            gpu.smart_complete_data()

        self.server.smart_complete_data()
        if self.usage.get_duration_hours() == 0:
            self.usage.hours_use_time = self._DEFAULT_TIME
        self.usage.smart_complete_data()
        self.usage.hours_electrical_consumption = self.dynamic_power()[0]

    def get_default_gpu(self) -> List[ComponentGPU]:
        return [ComponentGPU() for _ in range(self._DEFAULT_GPU_NUMBER)]

    def get_default_server(self) -> Server:
        return Server()
