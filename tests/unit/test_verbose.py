from boaviztapi.service.verbose import verbose_component, verbose_device


def test_verbose_component_cpu(empty_cpu, complete_cpu):
    assert verbose_component(complete_cpu, empty_cpu) == {
        'core_units': {'input_value': None, 'status': 'SET', 'used_value': 12},
        'die_size_per_core': {'input_value': None, 'status': 'SET', 'used_value': 0.245},
        'impacts': {'adp': 0.02, 'gwp': 16.0, 'pe': 247.0}}


def test_verbose_component_ram(empty_ram, complete_ram):
    assert verbose_component(complete_ram, empty_ram) == {
        'capacity': {'input_value': None, 'used_value': 32, 'status': 'SET'},
        'density': {'input_value': None, 'used_value': 1.79, 'status': 'SET'},
        'impacts': {'gwp': 45.0, 'pe': 562.0, 'adp': 0.003}}


def test_verbose_component_ssd(empty_ssd, complete_ssd):
    assert verbose_component(complete_ssd, empty_ssd) == {
        'capacity': {'input_value': None, 'used_value': 400, 'status': 'SET'},
        'density': {'input_value': None, 'used_value': 50.6, 'status': 'SET'},
        'impacts': {'gwp': 24.0, 'pe': 293.0, 'adp': 0.001}}


def test_verbose_component_power_supply(empty_power_supply, complete_power_supply):
    assert verbose_component(complete_power_supply, empty_power_supply) == {
        'unit_weight': {'input_value': None, 'used_value': 2.0, 'status': 'SET'},
        'impacts': {'gwp': 49.0, 'pe': 704.0, 'adp': 0.017}}


def test_verbose_component_case(empty_case, blade_case):
    assert verbose_component(blade_case, empty_case) == {
        'case_type': {'input_value': None, 'status': 'SET', 'used_value': 'blade'},
        'impacts': {'adp': 0.028, 'gwp': 86.0, 'pe': 1229.0}}


def test_verbose_usage(incomplete_usage, complete_usage):
    complete_usage.usage.smart_complete_data()
    assert verbose_component(complete_usage.usage, incomplete_usage.usage) == {
        'adp_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.0},
        'gwp_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.226},
        'hours_electrical_consumption': {'input_value': None, 'status': 'SET', 'used_value': 0.368985},
        'hours_use_time': {'input_value': None, 'status': 'SET', 'used_value': 1.0},
        'impacts': {'adp': 0.0, 'gwp': 0.0, 'pe': 0.0},
        'instance_per_server': {'input_value': None, 'status': 'SET', 'used_value': 4},
        'max_power': {'input_value': None, 'status': 'SET', 'used_value': 510.0},
        'pe_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.0},
        'usage_location': {'input_value': None, 'status': 'SET', 'used_value': 'EU27+1'}, 'workload': {
            '10': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.6},
                   'time': {'input_value': 0.4, 'status': 'MODIFY', 'used_value': 0.0}},
            '100': {'power': {'input_value': None, 'status': 'SET', 'used_value': 1.0},
                    'time': {'input_value': 0.2, 'status': 'MODIFY', 'used_value': 0.0}},
            '50': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.7235},
                   'time': {'input_value': 0.2, 'status': 'MODIFY', 'used_value': 1.0}},
            'idle': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.02},
                     'time': {'input_value': 0.2, 'status': 'MODIFY', 'used_value': 0.0}}}}


def test_verbose_device_server_1(empty_server, dell_r740):
    dell_r740.usage.smart_complete_data()
    assert verbose_device(dell_r740, empty_server) == {
        'CPU-1': {
            'unit': 2, 'hash': '5f75d18d9165b04381f24cb2130b62f756d266c45080982334585931482398ad',
            'core_units': {'input_value': None, 'used_value': 24, 'status': 'SET'},
            'die_size_per_core': {'input_value': None, 'used_value': 0.245, 'status': 'SET'},
            'impacts': {'gwp': 44.0, 'pe': 650.0, 'adp': 0.04}},
        'RAM-1': {'unit': 12, 'hash': '4985faa0d798469b3deea291f6e9852862e43a06f5364164e57801035cfa3410',
                  'capacity': {'input_value': None, 'used_value': 32, 'status': 'SET'},
                  'density': {'input_value': None, 'used_value': 1.79, 'status': 'SET'},
                  'impacts': {'gwp': 540.0, 'pe': 6744.0, 'adp': 0.036}},
        'SSD-1': {'unit': 1, 'hash': '41514f07d8fa09207407a0693c20b7647cba1751e658999a51b4c003fc032c91',
                  'capacity': {'input_value': None, 'used_value': 400, 'status': 'SET'},
                  'density': {'input_value': None, 'used_value': 50.6, 'status': 'SET'},
                  'impacts': {'gwp': 24.0, 'pe': 293.0, 'adp': 0.001}},
        'POWER_SUPPLY-1': {'unit': 2, 'hash': 'cdb1c15f77554bf77b8d8ccc2094af7ed72a8a19ff3f0fd0a9909ecacec06428',
                           'unit_weight': {'input_value': None, 'used_value': 2.99, 'status': 'SET'},
                           'impacts': {'gwp': 146.0, 'pe': 2104.0, 'adp': 0.05}},
        'CASE-1': {'case_type': {'input_value': None, 'status': 'SET', 'used_value': 'rack'},
                   'hash': '083dcd17f9997756af73de7c61f0cf2986b25075ad00bbf7c07e08cc80a2183f',
                   'impacts': {'adp': 0.02, 'gwp': 150.0, 'pe': 2200.0},
                   'unit': 1},
        'USAGE-1': {'adp_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.0},
                    'gwp_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.226},
                    'hash': 0, 'hours_electrical_consumption': {'input_value': None, 'status': 'SET',
                                                                'used_value': 0.35174445000000004},
                    'impacts': {'adp': 0.0, 'gwp': 696.0, 'pe': 0.0},
                    'max_power': {'input_value': None, 'status': 'SET', 'used_value': 510.0},
                    'pe_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.0}, 'unit': 1,
                    'usage_location': {'input_value': None, 'status': 'SET', 'used_value': 'EU27+1'}, 'workload': {
                '10': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.5118},
                       'time': {'input_value': None, 'status': 'SET', 'used_value': 0.2}},
                '100': {'power': {'input_value': None, 'status': 'SET', 'used_value': 1.0},
                        'time': {'input_value': None, 'status': 'SET', 'used_value': 0.15}},
                '50': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.7235},
                       'time': {'input_value': None, 'status': 'SET', 'used_value': 0.55}},
                'idle': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.3941},
                         'time': {'input_value': None, 'status': 'SET', 'used_value': 0.1}}},
                    'years_use_time': {'input_value': None, 'status': 'SET', 'used_value': 1}}}


def test_verbose_device_server_2(incomplete_server, completed_server_with_default):
    assert verbose_device(completed_server_with_default, incomplete_server) == {
        'RAM-1': {'unit': 24, 'hash': '4985faa0d798469b3deea291f6e9852862e43a06f5364164e57801035cfa3410',
                  'capacity': {'input_value': 32, 'used_value': 32, 'status': 'UNCHANGED'},
                  'density': {'input_value': 1.79, 'used_value': 1.79, 'status': 'UNCHANGED'},
                  'impacts': {'gwp': 1080.0, 'pe': 13488.0, 'adp': 0.072}},
        'SSD-1': {'unit': 2, 'hash': '41514f07d8fa09207407a0693c20b7647cba1751e658999a51b4c003fc032c91',
                  'capacity': {'input_value': 400, 'used_value': 400, 'status': 'UNCHANGED'},
                  'density': {'input_value': 50.6, 'used_value': 50.6, 'status': 'UNCHANGED'},
                  'impacts': {'gwp': 48.0, 'pe': 586.0, 'adp': 0.002}},
        'CASE-1': {'case_type': {'input_value': 'blade', 'status': 'UNCHANGED', 'used_value': 'blade'},
                   'hash': 'eee938fd3d9a958e767463266d8111ad53dddecc0f842120399e67479d7ad395',
                   'impacts': {'adp': 0.028, 'gwp': 86.0, 'pe': 1229.0},
                   'unit': 1},
        'MOTHERBOARD-1': {'unit': 1, 'hash': '3a31a8fbd4b871719831ef11af93eefbb1c2afc0f62d850a31fb5475aac9336e',
                          'impacts': {'gwp': 66.0, 'pe': 836.0, 'adp': 0.004}},
        'ASSEMBLY-1': {'unit': 1, 'hash': '8bfe70a2b59691c050865455cc9cf1b561ec702e7cf930c1026a490964bbd364',
                       'impacts': {'gwp': 7.0, 'pe': 69.0, 'adp': 0.0}},
        'CPU-1': {'unit': 2, 'hash': 'c8c7d224967280c8cb4cb95bfc1727e68645f38154310d2f8091170915f49464',
                  'core_units': {'input_value': None, 'used_value': 24, 'status': 'SET'},
                  'die_size_per_core': {'input_value': None, 'used_value': 0.245, 'status': 'SET'},
                  'impacts': {'gwp': 44.0, 'pe': 650.0, 'adp': 0.04}},
        'POWER_SUPPLY-1': {'unit': 2, 'hash': 'be84aabaaac41126e1bd93ec3c10b355c6c7534cf9e3d7337cef9d6d0bb116c6',
                           'unit_weight': {'input_value': None, 'used_value': 2.99, 'status': 'SET'},
                           'impacts': {'gwp': 146.0, 'pe': 2104.0, 'adp': 0.05}},
        'USAGE-1': {'adp_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.0},
                    'gwp_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.226}, 'hash': 0,
                    'hours_electrical_consumption': {'input_value': None, 'status': 'SET', 'used_value': 0.35175},
                    'impacts': {'adp': 0.0, 'gwp': 696.0, 'pe': 0.0},
                    'max_power': {'input_value': None, 'status': 'SET', 'used_value': 510},
                    'pe_factor': {'input_value': None, 'status': 'SET', 'used_value': 0.0}, 'unit': 1,
                    'usage_location': {'input_value': None, 'status': 'SET', 'used_value': 'EU27+1'}, 'workload': {
                '10': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.5117647058823529},
                       'time': {'input_value': None, 'status': 'SET', 'used_value': 0.19999999999999998}},
                '100': {'power': {'input_value': None, 'status': 'SET', 'used_value': 1.0},
                        'time': {'input_value': None, 'status': 'SET', 'used_value': 0.15}},
                '50': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.7235294117647059},
                       'time': {'input_value': None, 'status': 'SET', 'used_value': 0.5499999999999999}},
                'idle': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.3941176470588235},
                         'time': {'input_value': None, 'status': 'SET', 'used_value': 0.09999999999999999}},
                'off': {'power': {'input_value': None, 'status': 'SET', 'used_value': 0.0},
                        'time': {'input_value': None, 'status': 'SET', 'used_value': 0.0}}},
                    'years_use_time': {'input_value': None, 'status': 'SET', 'used_value': 1}}}
