from typing import Set, Optional

from boaviztapi.model.components.component import Component
from boaviztapi.model.devices.device import Device
from boaviztapi.model.ml_setup import MLSetup
import boaviztapi.utils.roundit as rd

_default_impacts_code = {"gwp", "pe", "adp"}


def bottom_up_setup(setup: MLSetup, impact_codes: Optional[Set[str]] = None) -> (dict, dict):
    setup.smart_complete_data()
    embodied_gwp = setup.embodied_impact_gwp()
    embodied_pe = setup.embodied_impact_pe()
    embodied_adp = setup.embodied_impact_adp()
    direct_gwp = setup.direct_impact_gwp()
    direct_pe = setup.direct_impact_pe()
    direct_adp = setup.direct_impact_adp()
    impacts = {
        'gwp': {
            'embodied': rd.round_to_sigfig(setup.psf*embodied_gwp[0], embodied_gwp[1]),
            'direct': rd.round_to_sigfig(setup.psf*direct_gwp[0], direct_gwp[1]),
            'unit': "kgCO2eq"
        },
        'pe': {
            'embodied': rd.round_to_sigfig(setup.psf*embodied_pe[0], embodied_pe[1]),
            'direct': rd.round_to_sigfig(setup.psf*direct_pe[0], direct_pe[1]),
            'unit': "MJ"
        },
        'adp': {
            'embodied': rd.round_to_sigfig(setup.psf*embodied_adp[0], embodied_adp[1]),
            'direct': rd.round_to_sigfig(setup.psf*direct_adp[0], direct_adp[1]),
            'unit': "kgSbeq"
        }
    }
    gwp_relative_SNBC = setup.gwp_relative_SNBC()
    gwp_relative_PB = setup.gwp_relative_PB()
    adp_relative_PB = setup.adp_relative_PB()
    perspective = {
        'relative_SNBC': {
            'value': rd.round_to_sigfig(setup.psf * gwp_relative_SNBC[0], gwp_relative_SNBC[1]),
            'unit': 'Emissions of X Person per year in a sustanability scenario'
        },
        'relative_PB_Climate_Change': {
            'value': rd.round_to_sigfig(setup.psf*gwp_relative_PB[0], gwp_relative_PB[1]),
            'unit': 'person'
        },
        'relative_PB_ADP': {
            'value': rd.round_to_sigfig(setup.psf*adp_relative_PB[0], adp_relative_PB[1]),
            'unit': 'person'
        }
    }
    return impacts, perspective


def bottom_up_device(device: Device, impact_codes: Optional[Set[str]] = None) -> dict:
    # Smart complete data
    device.smart_complete_data()

    impacts = {
        'gwp': {
            'manufacture': rd.round_to_sigfig(*device.impact_manufacture_gwp()),
            'use': rd.round_to_sigfig(*device.impact_use_gwp()),
            'unit': "kgCO2eq"
        },
        'pe': {
            'manufacture': rd.round_to_sigfig(*device.impact_manufacture_pe()),
            'use': rd.round_to_sigfig(*device.impact_use_pe()),
            'unit': "MJ"
        },
        'adp': {
            'manufacture': rd.round_to_sigfig(*device.impact_manufacture_adp()),
            'use': rd.round_to_sigfig(*device.impact_use_adp()),
            'unit': "kgSbeq"
        },
    }
    return impacts


def bottom_up_component(component: Component, units: int = 1, impact_codes: Optional[Set[str]] = None) -> dict:
    component.smart_complete_data()
    gwp = component.impact_gwp()
    pe = component.impact_pe()
    adp = component.impact_adp()

    impacts = {
        'gwp': {
            'manufacture': rd.round_to_sigfig(gwp[0]*units, gwp[1]),
            'use': "not implemented",
            'unit': "kgCO2eq"

        },
        'pe': {
            'manufacture': rd.round_to_sigfig(pe[0]*units, pe[1]),
            'use': "not implemented",
            'unit': "MJ"
        },
        'adp': {
            'manufacture': rd.round_to_sigfig(adp[0]*units, adp[1]),
            'use': "not implemented",
            'unit': "kgSbeq"
        },
    }
    return impacts
