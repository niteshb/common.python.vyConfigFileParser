from vyConfigFileParser import VyConfigFile, VyConfigFileBlock

class OSInfoBlock(VyConfigFileBlock):
    indentLevelMarkers = {
        0: { (None, 'os')               : {'target': None},},
        1: { ('family', '.*')           : {},
             ('version', '.*')          : {},},
    }

class ProcessorInfoBlock(VyConfigFileBlock):
    indentLevelMarkers = {
        0: { (None, 'processor')               : {'target': None},},
        1: { ('company', '(intel|amd|arm)')    : {},
             ('family', '.*')                  : {},
             ('clock-speed', '\d+ [MG]Hz')     : {},},
    }

class DeviceInfoFileBlock(VyConfigFileBlock):
    indentLevelMarkers = {
        0: [OSInfoBlock, ProcessorInfoBlock],
    }

devInfo = VyConfigFile('001.config.txt')
parsed = devInfo.parse(DeviceInfoFileBlock)
print(parsed)

class RudimentaryDeviceInfoBlock(VyConfigFileBlock):
    indentLevelMarkers = {
        0: { (None, '.*')               : {'target': 'device-info'},},
        1: { ('.*', '.*')               : {},},
    }
class RudimentaryDeviceInfoFileBlock(VyConfigFileBlock):
    indentLevelMarkers = {
        0: [RudimentaryDeviceInfoBlock],
    }
parsed = devInfo.parse(RudimentaryDeviceInfoFileBlock)
print(parsed)
