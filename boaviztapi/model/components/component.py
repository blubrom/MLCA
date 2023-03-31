import hashlib
import os
from abc import abstractmethod
from typing import Optional
import boaviztapi.utils.roundit as rd
import pandas as pd
from pydantic import BaseModel

from boaviztapi.model.components import data_dir

_cpu_df = pd.read_csv(os.path.join(data_dir, 'components/cpu_infos.csv'))
_ram_df = pd.read_csv(os.path.join(data_dir, 'components/ram_manufacture.csv'))
_ssd_df = pd.read_csv(os.path.join(data_dir, 'components/ssd_manufacture.csv'))
_cpu_df['manufacture_date'] = _cpu_df['manufacture_date'].astype(
    str)  # Convert date column to string
_gpu_df = pd.read_csv(os.path.join(
    data_dir, 'components/gpu_infos.csv'), skiprows=1)
_gpu_df['manufacture_date'] = _cpu_df['manufacture_date'].astype(
    str)  # Convert date column to string

# _gpu_tdp_df = pd.read_csv(os.path.join(
#     data_dir, 'components/GPU_TDP_Green_Algorithms.csv'), skiprows=1)
# _cpu_tdp_df = pd.read_csv(os.path.join(
#     data_dir, 'components/CPU_TDP_Green_Algorithms.csv'), skiprows=1)


class Component(BaseModel):
    hash: str = None
    TYPE: str = None

    @abstractmethod
    def impact_gwp(self) -> (float, int):
        pass

    @abstractmethod
    def impact_pe(self) -> (float, int):
        pass

    @abstractmethod
    def impact_adp(self) -> (float, int):
        pass

    @abstractmethod
    def smart_complete_data(self):
        pass

    @abstractmethod
    def power_draw(self) -> (float, int):
        pass

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def __hash__(self):
        object_fingerprint = bytes(
            ((type(self),) + tuple(self.__dict__.values())).__str__(), encoding='utf8')
        return hashlib.sha256(object_fingerprint).hexdigest()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hash = self.__hash__()


class ComponentCPU(Component):
    TYPE = "CPU"

    # figures come from: Gröger, J., Liu, R., Stobbe, L., Druschke, J., and Richter,N. (2021).
    # Green Cloud Computing: lebenszyklusbasierte Datenerhebung zuUmweltwirkungen des Cloud Computing:
    # Abschlussbericht.   Umweltbundesamt, Appendix B.2.1 and section 3.2.3.3
    # /!\ factor units is per cm² not per mm²
    _IMPACT_FACTOR_DICT = {
        "gwp": {
            # impact of producing 1cm² of die
            "die_impact": 1.97,
            # base impact (accounting for gold for the socket or the heatsink for instance)
            "impact": 9.14
        },
        "pe": {
            "die_impact": 26.50,
            "impact": 156.00
        },
        "adp": {
            "die_impact": 5.80E-07,
            "impact": 2.04E-02
        },
        # base die surface, this is obtained by a linear regression on
        # the die size as a function of the number of cores.
        # On their data, they obtained a CPU die area equal to 28.58 * number of cores + 49.157 (in mm²)
        "constant_core_impact": 0.491
    }

    _DEFAULT_CPU_DIE_SIZE_PER_CORE = 0.245

    _DEFAULT_CPU_CORE_UNITS = 24

   # Default value (Any) in the CPU_TDP_Green_Algorithms data
    _DEFAULT_TDP_PER_CORE = 12

    core_units: Optional[int] = None
    die_size: Optional[float] = None
    die_size_per_core: Optional[float] = None
    process: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None
    family: Optional[str] = None
    tdp: Optional[int] = None

    def impact_gwp(self) -> (float, int):
        core_impact = self._IMPACT_FACTOR_DICT['constant_core_impact']
        cpu_die_impact = self._IMPACT_FACTOR_DICT['gwp']['die_impact']
        cpu_impact = self._IMPACT_FACTOR_DICT['gwp']['impact']
        significant_figures = rd.min_significant_figures(
            self.die_size_per_core, core_impact, cpu_die_impact, cpu_impact)
        return (self.core_units * self.die_size_per_core + core_impact) * cpu_die_impact + cpu_impact, significant_figures

    def impact_pe(self) -> (float, int):
        core_impact = self._IMPACT_FACTOR_DICT['constant_core_impact']
        cpu_die_impact = self._IMPACT_FACTOR_DICT['pe']['die_impact']
        cpu_impact = self._IMPACT_FACTOR_DICT['pe']['impact']
        significant_figures = rd.min_significant_figures(
            self.die_size_per_core, core_impact, cpu_die_impact, cpu_impact)
        return (self.core_units * self.die_size_per_core + core_impact) * cpu_die_impact + cpu_impact, significant_figures

    def impact_adp(self) -> (float, int):
        core_impact = self._IMPACT_FACTOR_DICT['constant_core_impact']
        cpu_die_impact = self._IMPACT_FACTOR_DICT['adp']['die_impact']
        cpu_impact = self._IMPACT_FACTOR_DICT['adp']['impact']
        significant_figures = rd.min_significant_figures(
            self.die_size_per_core, core_impact, cpu_die_impact, cpu_impact)
        return (self.core_units * self.die_size_per_core + core_impact) * cpu_die_impact + cpu_impact, significant_figures

    def power_draw(self) -> (float, int):
        return self.tdp, 3

    def smart_complete_data(self):
        # TODO: refactor to include searching for the TDP and also getting the info
        # (die_size_per_core and core_units)from the CPU model name.
        if not self.tdp and self.model:
            sub = _cpu_tdp_df[_cpu_tdp_df['model'] == self.model]
            if len(sub) == 1:
                self.tdp = int(sub['TDP'])
                return
            else:
                print(
                    "nom de CPU inconnu, utilisation de la valeur par défaut pour le TDP")
        self.tdp = self._DEFAULT_TDP_PER_CORE * self._DEFAULT_CPU_CORE_UNITS

        if self.die_size_per_core and self.core_units:
            return

        elif self.die_size and self.core_units:
            self.die_size_per_core = self.die_size / self.core_units
            return

        # Let's infer the data
        else:
            sub = _cpu_df

            if self.family:
                sub = sub[sub['family'] == self.family]

            if self.core_units:
                sub = sub[sub['core_units'] == self.core_units]

            if len(sub) == 0 or len(sub) == len(_cpu_df):
                self.die_size_per_core = self._DEFAULT_CPU_DIE_SIZE_PER_CORE
                self.core_units = self._DEFAULT_CPU_CORE_UNITS

            elif len(sub) == 1:
                self.die_size_per_core = float(sub['die_size_per_core'])
                self.core_units = int(sub['core_units'])

            else:
                sub['_scope3'] = sub[['core_units', 'die_size_per_core']].apply(
                    lambda x: x[0] * x[1], axis=1)
                sub = sub.sort_values(by='_scope3', ascending=False)
                row = sub.iloc[0]
                die_size_per_core = float(row['die_size_per_core'])
                core_units = int(row['core_units'])
                self.die_size_per_core = die_size_per_core
                self.core_units = core_units


class ComponentRAM(Component):
    TYPE = "RAM"

    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "die_impact": 2.20,
            "impact": 5.22
        },
        "pe": {
            "die_impact": 27.30,
            "impact": 74.00
        },
        "adp": {
            "die_impact": 6.30E-05,
            "impact": 1.69E-03
        }
    }

    _DEFAULT_RAM_CAPACITY = 32
    _DEFAULT_RAM_DENSITY = 0.625

    # value taken from
    # Lannelongue, L., Grealey, J., Inouye, M., Green Algorithms: Quantifying the Carbon Footprint of Computation.
    # Adv. Sci. 2021, 8, 2100707. https://doi.org/10.1002/advs.202100707
    # citing reference 26.
    _POWER_DRAW_PER_GB = 0.3725

    capacity: Optional[int] = None
    density: Optional[float] = None
    process: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None
    integrator: Optional[str] = None

    def impact_gwp(self) -> (float, int):
        ram_die_impact = self._IMPACT_FACTOR_DICT['gwp']['die_impact']
        ram_impact = self._IMPACT_FACTOR_DICT['gwp']['impact']
        significant_figure = rd.min_significant_figures(
            self.density, ram_die_impact, ram_impact)
        return ((self.capacity / self.density) * ram_die_impact + ram_impact, significant_figure)

    def impact_pe(self) -> (float, int):
        ram_die_impact = self._IMPACT_FACTOR_DICT['pe']['die_impact']
        ram_impact = self._IMPACT_FACTOR_DICT['pe']['impact']
        significant_figure = rd.min_significant_figures(
            self.density, ram_die_impact, ram_impact)
        return (self.capacity / self.density) * ram_die_impact + ram_impact, significant_figure

    def impact_adp(self) -> (float, int):
        ram_die_impact = self._IMPACT_FACTOR_DICT['adp']['die_impact']
        ram_impact = self._IMPACT_FACTOR_DICT['adp']['impact']
        significant_figure = rd.min_significant_figures(
            self.density, ram_die_impact, ram_impact)
        return ((self.capacity / self.density) * ram_die_impact + ram_impact, significant_figure)

    def power_draw(self) -> (float, int):
        return self._POWER_DRAW_PER_GB * self.capacity, 3

    def smart_complete_data(self):
        if self.capacity and self.density:
            return
        else:
            sub = _ram_df

            if self.manufacturer:
                sub = sub[sub['manufacturer'] == self.manufacturer]

            if self.process:
                sub = sub[sub['process'] == self.process]

            if len(sub) == 0 or len(sub) == len(_cpu_df):
                self.capacity = self.capacity if self.capacity else self._DEFAULT_RAM_CAPACITY
                self.density = self._DEFAULT_RAM_DENSITY

            elif len(sub) == 1:
                self.capacity = self.capacity if self.capacity else self._DEFAULT_RAM_CAPACITY
                self.density = float(sub['density'])

            else:
                capacity = self.capacity if self.capacity else self._DEFAULT_RAM_CAPACITY
                sub['_scope3'] = sub['density'].apply(lambda x: capacity / x)
                sub = sub.sort_values(by='_scope3', ascending=False)
                density = float(sub.iloc[0].density)
                self.capacity = capacity
                self.density = density


class ComponentHDD(Component):
    TYPE = "HDD"

    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "impact": 31.10
        },
        "pe": {
            "impact": 276.00
        },
        "adp": {
            "impact": 2.50E-04
        }

    }

    capacity: Optional[int] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None

    def impact_gwp(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['gwp']['impact'], 4

    def impact_pe(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['pe']['impact'], 3

    def impact_adp(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['adp']['impact'], 3

    def power_draw(self) -> (float, int):
        # TODO: explore some ressources about the consumption of storage
        return 0, 3

    def smart_complete_data(self):
        pass


class ComponentSSD(Component):
    TYPE = "SSD"

    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "die_impact": 2.20,
            "impact": 6.34
        },
        "pe": {
            "die_impact": 27.30,
            "impact": 76.90
        },
        "adp": {
            "die_impact": 6.30E-05,
            "impact": 5.63E-04
        }
    }

    _DEFAULT_SSD_CAPACITY = 1000
    _DEFAULT_SSD_DENSITY = 48.5

    capacity: Optional[int] = None
    density: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None

    def impact_gwp(self) -> (float, int):
        ssd_die_impact = self._IMPACT_FACTOR_DICT['gwp']['die_impact']
        ssd_impact = self._IMPACT_FACTOR_DICT['gwp']['impact']
        significant_figure = rd.min_significant_figures(
            self.density, ssd_impact, ssd_die_impact)
        return (self.capacity / self.density) * ssd_die_impact + ssd_impact, significant_figure

    def impact_pe(self) -> (float, int):
        ssd_die_impact = self._IMPACT_FACTOR_DICT['pe']['die_impact']
        ssd_impact = self._IMPACT_FACTOR_DICT['pe']['impact']
        significant_figure = rd.min_significant_figures(
            self.density, ssd_impact, ssd_die_impact)
        return (self.capacity / self.density) * ssd_die_impact + ssd_impact, significant_figure

    def impact_adp(self) -> (float, int):
        ssd_die_impact = self._IMPACT_FACTOR_DICT['adp']['die_impact']
        ssd_impact = self._IMPACT_FACTOR_DICT['adp']['impact']
        significant_figure = rd.min_significant_figures(
            self.density, ssd_impact, ssd_die_impact)
        return (self.capacity / self.density) * ssd_die_impact + ssd_impact, significant_figure

    def power_draw(self) -> (float, int):
        # TODO: explore some ressources about the consumption of storage
        return 0, 3

    def smart_complete_data(self):
        if self.capacity and self.density:
            return
        else:
            sub = _ssd_df

            if self.manufacturer:
                sub = sub[sub['manufacturer'] == self.manufacturer]

            if len(sub) == 0 or len(sub) == len(_cpu_df):
                self.capacity = self.capacity if self.capacity else self._DEFAULT_SSD_CAPACITY
                self.density = self.density if self.density else self._DEFAULT_SSD_DENSITY

            elif len(sub) == 1:
                self.capacity = self.capacity if self.capacity else self._DEFAULT_SSD_CAPACITY
                self.density = float(sub['density'])

            else:
                capacity = self.capacity if self.capacity else self._DEFAULT_SSD_CAPACITY
                sub['_scope3'] = sub['density'].apply(lambda x: capacity / x)
                sub = sub.sort_values(by='_scope3', ascending=False)
                density = float(sub.iloc[0].density)
                self.capacity = capacity
                self.density = density


class ComponentPowerSupply(Component):
    TYPE = "POWER_SUPPLY"
    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "impact": 24.30
        },
        "pe": {
            "impact": 352.00
        },
        "adp": {
            "impact": 8.30E-03
        }
    }

    _DEFAULT_POWER_SUPPLY_WEIGHT = 2.99

    unit_weight: Optional[float] = None

    def impact_gwp(self) -> (float, int):
        power_supply_weight = self.unit_weight
        power_supply_impact = self._IMPACT_FACTOR_DICT['gwp']['impact']
        return power_supply_weight * power_supply_impact, 4

    def impact_pe(self) -> (float, int):
        power_supply_weight = self.unit_weight
        power_supply_impact = self._IMPACT_FACTOR_DICT['pe']['impact']
        return power_supply_weight * power_supply_impact, 3

    def impact_adp(self) -> (float, int):
        power_supply_weight = self.unit_weight
        power_supply_impact = self._IMPACT_FACTOR_DICT['adp']['impact']
        return power_supply_weight * power_supply_impact, 3

    def power_draw(self) -> (float, int):
        return 0, 3

    def smart_complete_data(self):
        self.unit_weight = self.unit_weight \
            if self.unit_weight is not None else \
            self._DEFAULT_POWER_SUPPLY_WEIGHT


class ComponentMotherBoard(Component):
    TYPE = "MOTHERBOARD"
    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "impact": 66.10
        },
        "pe": {
            "impact": 836.00
        },
        "adp": {
            "impact": 3.69E-03
        }
    }

    def impact_gwp(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['gwp']['impact'], 4

    def impact_pe(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['pe']['impact'], 3

    def impact_adp(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['adp']['impact'], 3

    def power_draw(self) -> (float, int):
        # Lannelongue, L., Grealey, J., Inouye, M., Green Algorithms: Quantifying the Carbon Footprint of Computation.
        # Adv. Sci. 2021, 8, 2100707. https://doi.org/10.1002/advs.202100707
        # Says that the power draw of the Motherboard is negligible
        return 0, 3

    def smart_complete_data(self):
        pass


class ComponentCase(Component):
    TYPE = "CASE"
    case_type: str = None
    _IMPACT_FACTOR_DICT = {
        "rack": {
            "gwp": {
                "impact": 150.00
            },
            "pe": {
                "impact": 2200.00

            },
            "adp": {
                "impact": 2.02E-02
            }
        },
        "blade": {
            "gwp": {
                "impact_blade_server": 30.90,
                "impact_blade_16_slots": 880.00
            },
            "pe": {
                "impact_blade_server": 435.00,
                "impact_blade_16_slots": 12700.00
            },
            "adp": {
                "impact_blade_server": 6.72E-04,
                "impact_blade_16_slots": 4.32E-01
            }
        }

    }

    def impact_gwp(self) -> (float, int):
        if self.case_type == "blade":
            impact_blade_16_slots = self._IMPACT_FACTOR_DICT['blade']['gwp']['impact_blade_16_slots']
            impact_blade_server = self._IMPACT_FACTOR_DICT['blade']['gwp']['impact_blade_server']
            sigfig = rd.min_significant_figures(
                impact_blade_16_slots, impact_blade_server)
            return (impact_blade_16_slots / 16) + impact_blade_server, sigfig
        else:
            return self._IMPACT_FACTOR_DICT['rack']['gwp']['impact'], 5

    def impact_pe(self) -> (float, int):
        if self.case_type == "blade":
            impact_blade_16_slots = self._IMPACT_FACTOR_DICT['blade']['pe']['impact_blade_16_slots']
            impact_blade_server = self._IMPACT_FACTOR_DICT['blade']['pe']['impact_blade_server']
            sigfig = rd.min_significant_figures(
                impact_blade_16_slots, impact_blade_server)
            return (impact_blade_16_slots / 16) + impact_blade_server, sigfig
        else:
            return self._IMPACT_FACTOR_DICT['rack']['pe']['impact'], 4

    def impact_adp(self) -> (float, int):
        if self.case_type == "blade":
            impact_blade_16_slots = self._IMPACT_FACTOR_DICT['blade']['adp']['impact_blade_16_slots']
            impact_blade_server = self._IMPACT_FACTOR_DICT['blade']['adp']['impact_blade_server']
            sigfig = rd.min_significant_figures(
                impact_blade_16_slots, impact_blade_server)
            return (impact_blade_16_slots / 16) + impact_blade_server, sigfig
        else:
            return self._IMPACT_FACTOR_DICT['rack']['adp']['impact'], 3

    def power_draw(self) -> (float, int):
        # Does not consume anything
        # One would maybe want to take into account fans in this place
        # if they were to have a non negligible consumption
        return 0, 3

    def smart_complete_data(self):
        if self.case_type is None:
            self.case_type = "rack"


class ComponentAssembly(Component):
    TYPE = "ASSEMBLY"

    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "impact": 6.68

        },
        "pe": {
            "impact": 68.60

        },
        "adp": {
            "impact": 1.41E-06
        }
    }

    def impact_gwp(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['gwp']['impact'], 3

    def impact_pe(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['pe']['impact'], 3

    def impact_adp(self) -> (float, int):
        return self._IMPACT_FACTOR_DICT['adp']['impact'], 3

    def power_draw(self) -> (float, int):
        # by definition does not take place during usage so
        # a value of 0 is chosen
        return 0, 3

    def smart_complete_data(self):
        pass


class ComponentGPU(Component):
    TYPE = "GPU"

    # impact factors chosen are the same as for CPUs for now
    # die impacts should not change but base impacts should,
    # once we gather specific data from at leat a GPU
    # /!\ factor units is per cm² not per mm²
    # for more details on what each quantity stands for, look at CPU._IMPACT_FACTOR_DICT
    _IMPACT_FACTOR_DICT = {
        "gwp": {
            "die_impact": 1.97,
            "impact": 9.14
        },
        "pe": {
            "die_impact": 26.50,
            "impact": 156.00
        },
        "adp": {
            "die_impact": 5.80E-07,
            "impact": 2.04E-02
        },
    }

    # mean of the values in the database.
    _DEFAULT_GPU_TDP = 220
    # in cm²
    _DEFAULT_GPU_DIE_SIZE = 5.83
    # in GB
    _DEFAULT_GPU_MEMORY = 23

    die_size: Optional[float] = None
    process: Optional[float] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    model: Optional[str] = None
    architecture: Optional[str] = None
    tdp: Optional[int] = None
    memory_size: Optional[int] = None
    memory: Optional[ComponentRAM] = None

    def impact_gwp(self) -> (float, int):
        gpu_die_impact = self._IMPACT_FACTOR_DICT['gwp']['die_impact']
        gpu_impact = self._IMPACT_FACTOR_DICT['gwp']['impact']
        significant_figures = rd.min_significant_figures(
            self.die_size, gpu_die_impact, gpu_impact)
        return self.die_size * gpu_die_impact + gpu_impact, significant_figures

    def impact_pe(self) -> (float, int):
        gpu_die_impact = self._IMPACT_FACTOR_DICT['pe']['die_impact']
        gpu_impact = self._IMPACT_FACTOR_DICT['pe']['impact']
        significant_figures = rd.min_significant_figures(
            self.die_size, gpu_die_impact, gpu_impact)
        return self.die_size * gpu_die_impact + gpu_impact, significant_figures

    def impact_adp(self) -> (float, int):
        gpu_die_impact = self._IMPACT_FACTOR_DICT['adp']['die_impact']
        gpu_impact = self._IMPACT_FACTOR_DICT['adp']['impact']
        significant_figures = rd.min_significant_figures(
            self.die_size, gpu_die_impact, gpu_impact)
        return self.die_size * gpu_die_impact + gpu_impact, significant_figures

    def power_draw(self) -> (float, int):
        return self.tdp, 3

    def smart_complete_data(self):
        # first complete infos about the TDP, the die size and the memory size
        if not (self.tdp and self.die_size and self.memory_size):
            sub = _gpu_df
            if self.model:
                sub = sub[sub['model'] == self.model]
            if self.tdp:
                sub = sub[sub['TDP'] == self.tdp]
            if self.die_size:
                sub = sub[sub['die_size'] == self.die_size]
            if self.architecture:
                sub = sub[sub['architecture'] == self.architecture]
            if self.process:
                sub = sub[sub['process'] == self.process]
            if self.manufacture_date:
                sub = sub[sub['manufacture_date'] == self.manufacture_date]

            if len(sub) == 0 or len(sub) == len(_cpu_df):
                # TODO: savoir renvoyer un log disant que le nom est inconnu
                # pour cela, regarder la doc de fastapi, au moins pour le test
                # à terme, ce ne sera pas forcément nécéssaire vu qu'on peut faire l'hypothèse que les données arriveront depuis
                # un formulaire. Cette hypothèse n'est cependant pas forcément réaliste si on souhaite pouvoir utiliser cette api
                # en mode "mesure"
                # Si je comprends la doc, faire un print pourrait donner un résultat : essayons donc.
                print("nom de GPU inconnu, utilisation des valeurs par défaut")
                self.die_size = self._DEFAULT_GPU_DIE_SIZE
                self.tdp = self._DEFAULT_GPU_TDP
                self.memory_size = self._DEFAULT_GPU_MEMORY
            elif len(sub) == 1:
                self.tdp = int(sub['TDP'])
                self.die_size = float(sub['die_size'])
                self.memory_size = int(sub['memory'])
            else:
                self.tdp = sub['TDP'].mean()
                self.die_size = sub['die_size'].mean()
                self.memory_size = int(sub['memory'].mean())
        # then,
        self.memory = ComponentRAM()
        self.memory.capacity = self.memory_size
        self.memory.smart_complete_data()
