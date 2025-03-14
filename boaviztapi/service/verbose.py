from boaviztapi.model.components.component import Component
from boaviztapi.model.devices.device import Device
from boaviztapi.model.ml_setup import MLSetup
import boaviztapi.utils.roundit as rd
import copy


def verbose_setup(complete_setup: MLSetup, input_setup: MLSetup):
    json_output = {}
    complete_setup = copy.deepcopy(complete_setup)
    old_dynamic_ratio = complete_setup.usage.dynamic_ratio
    complete_setup.usage.dynamic_ratio = 1
    usage_gpus = copy.deepcopy(complete_setup.usage)
    usage_gpus.hours_electrical_consumption = complete_setup.gpu_usage * \
        sum(g.power_draw()[0] for g in complete_setup.gpus) / 1000
    usage_gpus.dynamic_ratio = 1
    usage_ram = copy.deepcopy(complete_setup.usage)
    usage_ram.hours_electrical_consumption = sum(
        r.power_draw()[0] for r in complete_setup.server.config_components if r.TYPE == 'RAM') / 1000
    usage_ram.dynamic_ratio = 1
    usage_cpu = copy.deepcopy(complete_setup.usage)
    usage_cpu.hours_electrical_consumption = complete_setup.cpu_usage * \
        sum(c.power_draw()[0]
            for c in complete_setup.server.config_components if c.TYPE == 'CPU') / 1000
    usage_cpu.dynamic_ratio = 1
    complete_setup.usage.dynamic_ratio = old_dynamic_ratio

    for attr in ['nb_nodes', 'psf', 'cpu_usage', 'gpu_usage', 'average_usage', 'hardware_replacement_rate']:
        json_output[attr] = {}
        json_output[attr]["input_value"] = getattr(input_setup, attr, None)
        json_output[attr]["used_value"] = getattr(complete_setup, attr, None)
        json_output[attr]["status"] = get_status(json_output[attr]["used_value"], json_output[attr]["input_value"])



    gwp_gpu = usage_gpus.impact_gwp()
    gwp_ram = usage_ram.impact_gwp()
    gwp_cpu = usage_cpu.impact_gwp()
    pe_gpu = usage_gpus.impact_pe()
    pe_ram = usage_ram.impact_pe()
    pe_cpu = usage_cpu.impact_pe()
    adp_gpu = usage_gpus.impact_adp()
    adp_ram = usage_ram.impact_adp()
    adp_cpu = usage_cpu.impact_adp()

    json_output["usage"] = verbose_component(
        complete_setup.usage, input_setup.usage)

    json_output['dynamic energy consumption'] = {
        'value': rd.round_to_sigfig(*complete_setup.usage.dynamic_energy_consumption()),
        'unit': "kWh"
    }

    json_output["embodied impacts"] = {
        'gwp': {
            'server': rd.round_to_sigfig(*complete_setup.gwp_embodied_server),
            'gpus': rd.round_to_sigfig(*complete_setup.gwp_embodied_gpus),
            'unit': "kgCO2eq"
        },

        'pe': {
            'server': rd.round_to_sigfig(*complete_setup.pe_embodied_server),
            'gpus': rd.round_to_sigfig(*complete_setup.pe_embodied_gpus),
            'unit': "MJ"
        },
        'adp': {
            'server': rd.round_to_sigfig(*complete_setup.adp_embodied_server),
            'gpus': rd.round_to_sigfig(*complete_setup.adp_embodied_gpus),
            'unit': "kgSbeq"
        }
    }

    json_output["dynamic impacts"] = {
        'gwp': {
            'value': rd.round_to_sigfig(complete_setup.nb_nodes * complete_setup.usage.dynamic_impact_gwp[0], complete_setup.usage.dynamic_impact_gwp[1]),
            'gpus': rd.round_to_sigfig(complete_setup.nb_nodes * gwp_gpu[0], gwp_gpu[1]),
            'ram': rd.round_to_sigfig(complete_setup.nb_nodes * gwp_ram[0], gwp_ram[1]),
            'cpus': rd.round_to_sigfig(complete_setup.nb_nodes * gwp_cpu[0], gwp_cpu[1]),
            'unit': "kgCO2eq"
        },
        'pe': {
            'value': rd.round_to_sigfig(complete_setup.nb_nodes * complete_setup.usage.dynamic_impact_pe[0], complete_setup.usage.dynamic_impact_pe[1]),
            'gpus': rd.round_to_sigfig(complete_setup.nb_nodes * pe_gpu[0], pe_gpu[1]),
            'ram': rd.round_to_sigfig(complete_setup.nb_nodes * pe_ram[0], pe_ram[1]),
            'cpus': rd.round_to_sigfig(complete_setup.nb_nodes * pe_cpu[0], pe_cpu[1]),
            'unit': "MJ"
        },
        'adp': {
            'value': rd.round_to_sigfig(complete_setup.nb_nodes * complete_setup.usage.dynamic_impact_adp[0], complete_setup.usage.dynamic_impact_adp[1]),
            'gpus': rd.round_to_sigfig(complete_setup.nb_nodes * adp_gpu[0], adp_gpu[1]),
            'ram': rd.round_to_sigfig(complete_setup.nb_nodes * adp_ram[0], adp_ram[1]),
            'cpus': rd.round_to_sigfig(complete_setup.nb_nodes * adp_cpu[0], adp_cpu[1]),
            'unit': "kgSbeq"
        }
    }
    json_output["manufacture of one server node"] = verbose_device(
        complete_device=complete_setup.server, input_device=input_setup.server)
    # we do not want this part that was automaticaly added when completing the server
    del json_output["manufacture of one server node"]["USAGE-1"]
    json_output["manufacture of one gpu"] = verbose_component(
        complete_component=complete_setup.gpus[0], input_component=input_setup.gpus[0])
    return json_output


def verbose_device(complete_device: Device, input_device: Device):
    json_output = {}

    input_components = input_device.config_components
    complete_components = complete_device.config_components

    input_components.append(input_device.usage)
    complete_components.append(complete_device.usage)

    for complete_component in complete_components:
        component_type = complete_component.TYPE
        done = False
        i = 1

        while True:
            component_name = component_type + "-" + str(i)
            if json_output.get(component_name) is None:
                json_output[component_name] = {}
                json_output[component_name]["unit"] = 1
                break
            elif complete_component.hash == json_output[component_name].get("hash"):
                json_output[component_name]["unit"] += 1
                done = True
                break
            i += 1
        if done:
            continue

        matching_component = None
        for item in input_components:
            if complete_component.hash == item.hash:
                matching_component = item
                break

        json_output[component_name]["hash"] = complete_component.hash

        json_output[component_name] = {**json_output[component_name],
                                       **verbose_component(complete_component=complete_component,
                                                           input_component=matching_component)}

    for item in json_output:
        json_output[item]["impacts"]["gwp"] = {
            'value': json_output[item]["impacts"]["gwp"]['value'] * json_output[item]["unit"],
            'unit': "kgCO2eq"}
        json_output[item]["impacts"]["pe"] = {
            'value': json_output[item]["impacts"]["pe"]['value'] * json_output[item]["unit"],
            'unit': "MJ"}
        json_output[item]["impacts"]["adp"] = {
            'value': json_output[item]["impacts"]["adp"]['value'] * json_output[item]["unit"],
            'unit': "kgSbeq"}

    return json_output


def verbose_component(complete_component: Component, input_component: Component, units: int = None):
    json_output = {}

    if units:
        json_output["units"] = units

    for attr, value in complete_component.__iter__():
        if type(value) is dict:
            json_output[attr] = \
                recursive_dict_verbose(value,
                                       {} if getattr(input_component, attr) is None else getattr(input_component, attr))
        elif value is not None and attr != "TYPE" and attr != "hash":
            if complete_component.TYPE == "GPU" and attr == "memory":
                json_output[attr] = verbose_component(
                    complete_component=complete_component.memory, input_component=input_component.memory)
            else:
                json_output[attr] = {}
                json_output[attr]["input_value"] = getattr(
                    input_component, attr, None)
                json_output[attr]["used_value"] = value
                json_output[attr]["status"] = get_status(
                    json_output[attr]["used_value"], json_output[attr]["input_value"])

    json_output["impacts"] = {"gwp": {
        "value": rd.round_to_sigfig(*complete_component.impact_gwp()),
        "unit": "kgCO2eq"},
        "pe": {
            "value": rd.round_to_sigfig(*complete_component.impact_pe()),
            "unit": "MJ"},
        "adp": {"value": rd.round_to_sigfig(*complete_component.impact_adp()),
                "unit": "kgSbeq"},
    }
    return json_output


def recursive_dict_verbose(dict1, dict2):
    json_output = {}
    for attr, value in dict1.items():
        if type(value) is dict:
            json_output[attr] = recursive_dict_verbose(
                value, dict2.get(attr, {}))
        elif value is not None:
            json_output[attr] = {}
            json_output[attr]["input_value"] = dict2.get(attr)
            json_output[attr]["used_value"] = value
            json_output[attr]["status"] = get_status(
                json_output[attr]["used_value"], json_output[attr]["input_value"])
    return json_output


def get_status(usedt_value, input_value):
    if usedt_value == input_value:
        return "UNCHANGED"
    elif input_value is None:
        return "SET"
    else:
        return "MODIFY"
