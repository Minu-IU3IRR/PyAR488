from PyAR488.PyAR488 import AR488
interface = AR488('COM5')


class HP436A:
    from PyAR488.PyAR488 import AR488

    _measure = {
        'W' : 'A',
        'dB_rel' : 'B',
        'dB_ref'  :'C',
        'dBm' : 'D',
    }
    
    _measurement_rate = {
        'hold' : 'H',
        'trigger_settling' : 'T',
        'trigger_immediate' : 'I',
        'free_run_fast' : 'R',
        'free_run' : 'V'
    }

    def __init__(self, interface:AR488, address:int) -> None:
        self.interface = interface
        self.address = address

        self.mode = None
        self.range = None
        self.cal_factor_enabled = True

    class UnderRange(Exception):
        def __init__(self):
            super().__init__("Watt under range")

    class OverRange(Exception):
        def __init__(self) -> None:
            super().__init__("Over range condition")
    
    class AutoZeroInProgress(Exception):
        def __init__(self):
            super().__init__("sensor zero in progress")
    
    class AutoZeroOverRange(Exception):
        def __init__(self):
            super().__init__("Power detected when performig auto zero")

    def _write(self, message:str):
        self.interface.address(self.address)
        self.interface.bus_write(message)

    def _read(self):
        self.interface.address(self.address)
        return self.interface.read()

    def read(self, all_data = True):
        data = self._read()  # -> b'PKD 0002E-02\r\n'  {'mode': 68, 'range': 75, 'reading': 0.02, 'status': 80}
        #p -> measured value valid
        #k-> range middle
        #d -> dBm
        # 0002-> measired value
        # -> E-02
        # -> CR+LF
        if len(data) == 0:
            return None  # instrument buisy or no data found
        
        status = data[0]
        if status == 'Q':
            raise self.UnderRange  # watt specitic
        elif status == 'R':
            raise self.OverRange
        elif status == 'S':
            raise self.UnderRange  # dBm specific
        elif status == 'T' or status == 'U':
            raise self.AutoZeroInProgress
        elif status == 'V':
            raise self.AutoZeroOverRange
        
        # P == good

        self.range = data[1]
        self.mode = data[2]
        
        if data[3] == ' ':  #space = positive
            reading = (data[4:8])
        else:  # minus sign
            reading = float(data[3:8])
        exponent = -int(data[10:12])
        reading = reading * 10 ** exponent

        if all_data:
            return {
                'range' : self.range,
                'mode' : self.mode,
                'reading' : reading,
                'status' : status
            }
        else:
            return reading
    
    def autozero(self):
        self._write('Z')

    def enable_cal_factor(self, enable = True):
        if enable:
            self._write('-')
            self.cal_factor_enabled = True
        else:
            self._write('+')
            self.cal_factor_enabled = False
    
    def set_measurement_rate(self, rate:str):
        if rate in self._measurement_rate:
            self._write(self._measurement_rate[rate])
        else:
            raise Exception('invalid measurement rate')
        

meter = HP436A(interface, 13)

from time import sleep
from pprint import pprint
while True:
    pprint(meter.read(all_data=True))
    sleep(0.5)