import os
from abc import abstractmethod

import pandas as pd

from typing import Dict, Optional

from boaviztapi.model.components import data_dir
from boaviztapi.model.components.component import Component
import boaviztapi.utils.roundit as rd

_electricity_emission_factors_df = pd.read_csv(os.path.join(
    data_dir, 'electricity/electricity_impact_factors.csv'))

DEFAULT_SIG_FIGURES: int = 3


class Usage(Component):
    TYPE = "USAGE"

    years_use_time: Optional[float] = None
    days_use_time: Optional[float] = None
    hours_use_time: Optional[float] = None

    hours_electrical_consumption: Optional[float] = None
    usage_location: Optional[str] = None

    gwp_factor: Optional[float] = None
    pe_factor: Optional[float] = None
    adp_factor: Optional[float] = None

    _DEFAULT_USAGE_LOCATION = "EEE"
    _DEFAULT_YEAR_USE_TIME = 1

    @abstractmethod
    def impact_gwp(self) -> (float, int):
        return self.hours_electrical_consumption * self.get_duration_hours() * self.gwp_factor, DEFAULT_SIG_FIGURES

    @abstractmethod
    def impact_pe(self) -> (float, int):
        return self.hours_electrical_consumption * self.get_duration_hours() * self.pe_factor, DEFAULT_SIG_FIGURES

    @abstractmethod
    def impact_adp(self) -> (float, int):
        return self.hours_electrical_consumption * self.get_duration_hours() * self.adp_factor, DEFAULT_SIG_FIGURES

    @abstractmethod
    def power_draw(self) -> (float, int):
        return self.hours_electrical_consumption, 3

    @abstractmethod
    def get_hours_electrical_consumption(self):
        pass

    @abstractmethod
    def get_duration_hours(self) -> float:
        return (self.hours_use_time or 0) + ((self.days_use_time or 0) * 24) + ((self.years_use_time or 0) * 365 * 24)

    @abstractmethod
    def smart_complete_data(self):

        if self.usage_location is None:
            self.usage_location = self._DEFAULT_USAGE_LOCATION
        else:
            sub = _electricity_emission_factors_df
            sub = sub[sub['code'] == self.usage_location]
            if len(sub) == 0:
                self.usage_location = self._DEFAULT_USAGE_LOCATION

        if self.years_use_time is None and self.days_use_time is None and self.hours_use_time is None:
            self.years_use_time = self._DEFAULT_YEAR_USE_TIME

        if self.gwp_factor is None:
            sub = _electricity_emission_factors_df
            sub = sub[sub['code'] == self.usage_location]
            self.gwp_factor = float(sub['gwp_emission_factor'])

        if self.pe_factor is None:
            sub = _electricity_emission_factors_df
            sub = sub[sub['code'] == self.usage_location]
            self.pe_factor = float(sub['pe_emission_factor'])

        if self.adp_factor is None:
            sub = _electricity_emission_factors_df
            sub = sub[sub['code'] == self.usage_location]
            self.adp_factor = float(sub['adpe_emission_factor'])

    def __hash__(self) -> int:
        # TODO: TO ENHANCE
        return 0


class UsageServer(Usage):
    # TODO: Set dfault workload ratio and corresponding power of DELL R740 LCA
    _DEFAULT_MAX_POWER = 510

    _DEFAULT_WORKLOAD = {"100": {"time": (3.6 / 24), "power": 1.0},
                         "50": {"time": (13.2 / 24), "power": 369 / 510},
                         "10": {"time": (4.8 / 24), "power": 261 / 510},
                         "idle": {"time": (2.4 / 24), "power": 201 / 510},
                         "off": {"time": 0., "power": 0.}
                         }

    max_power: Optional[float] = None
    workload: Optional[Dict[str, Dict[str, float]]] = None

    def impact_gwp(self) -> (float, int):
        return super().impact_gwp()[0], 3

    def impact_pe(self) -> (float, int):
        return super().impact_pe()[0], 3

    def impact_adp(self) -> (float, int):
        return super().impact_adp()[0], 3

    def power_draw(self) -> (float, int):
        return super().power_draw()

    def get_hours_electrical_consumption(self) -> float:
        hours_electrical_consumption = 0
        for values in self.workload.values():
            hours_electrical_consumption += values["time"] * \
                values["power"] * self.max_power
        return hours_electrical_consumption / 1000

    def smart_complete_data(self):
        super().smart_complete_data()
        if self.hours_electrical_consumption is None:
            if self.max_power is None:
                self.max_power = self._DEFAULT_MAX_POWER
            if self.workload is None:
                self.workload = self._DEFAULT_WORKLOAD

            self.hours_electrical_consumption = self.get_hours_electrical_consumption()

    def get_duration_hours(self) -> float:
        return super().get_duration_hours()


class UsageCloud(UsageServer):
    instance_per_server: Optional[float] = None

    def impact_gwp(self) -> (float, int):
        return super().impact_gwp()

    def impact_pe(self) -> (float, int):
        return super().impact_pe()

    def impact_adp(self) -> (float, int):
        return super().impact_adp()

    def smart_complete_data(self):
        super().smart_complete_data()

    def get_duration_hours(self) -> float:
        return super().get_duration_hours()


class UsageSetup(Usage):

    dynamic_ratio: Optional[float] = None
    minute_use_time: Optional[float] = None
    # default ratio computed from BLOOM analysis data
    # over a period of a month:
    # infrastructure mode : 223 kWh
    # idle mode : 887 kWh
    # production mode : 1310 kWh
    _DEFAULT_DYNAMIC_RATIO = 200/109
    _DEFAULT_YEAR_USE_TIME = 0

    dynamic_impact_gwp: Optional[float] = None
    dynamic_impact_adp: Optional[float] = None
    dynamic_impact_pe: Optional[float] = None

    def impact_gwp(self) -> (float, int):
        i, s = super().impact_gwp()
        self.dynamic_impact_gwp = i, s
        return i * self.dynamic_ratio, s

    def impact_pe(self) -> (float, int):
        i, s = super().impact_pe()
        self.dynamic_impact_pe = i, s
        return i * self.dynamic_ratio, s

    def impact_adp(self) -> (float, int):
        i, s = super().impact_adp()
        self.dynamic_impact_adp = i, s
        return i * self.dynamic_ratio, s

    def smart_complete_data(self):
        super().smart_complete_data()
        if self.dynamic_ratio is None:
            self.dynamic_ratio = self._DEFAULT_DYNAMIC_RATIO

    def get_hours_electrical_consumption(self):
        return super().get_hours_electrical_consumption()

    def get_duration_hours(self):
        return super().get_duration_hours() + (self.minute_use_time or 0) / 60

    def power_draw(self) -> (float, int):
        return super().power_draw()

    def energy_consumption(self):
        return self.hours_electrical_consumption * self.dynamic_ratio * self.get_duration_hours(), DEFAULT_SIG_FIGURES

    def dynamic_energy_consumption(self):
        return self.hours_electrical_consumption * self.get_duration_hours(), DEFAULT_SIG_FIGURES
