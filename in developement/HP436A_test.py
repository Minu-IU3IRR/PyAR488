from time import sleep
from PyAR488.PyAR488 import AR488
interface = AR488('COM5')


class HP436A:
    from PyAR488.PyAR488 import AR488

    _mode = {
        'W': 'A',
        'dB_rel': 'B',
        'dB_ref': 'C',
        'dBm': 'D',
    }

    _measurement_rate = {
        'hold': 'H',
        'trigger_settling': 'T',
        'trigger_immediate': 'I',
        'free_run_fast': 'R',
        'free_run': 'V'
    }

    _range = {'I': 1, 'J': 2, 'K': 3, 'L': 4, 'M': 5}

    def __init__(self, interface: AR488, address: int) -> None:
        self.interface = interface
        self.address = address

        self.status = None
        self.range = None
        self.mode = None
        self.cal_factor_enabled = True

    # internals

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

    def _write(self, message: str):
        self.interface.address(self.address)
        self.interface.bus_write(message)

    def _read(self):
        self.interface.address(self.address)
        return self.interface.read(decode=True)

    # functions
    def read(self, all_data=True):
        """returns the reading of the instrument or throws an exception based on the problem,
        the reading unit is defined using the 'set_measurement_rate' function. use parameter all_data to query all data about the reading"""
        data = self._read(
        )  # -> b'PKD 0002E-02\r\n'  {'mode': 68, 'range': 75, 'reading': 0.02, 'status': 80}
        if len(data) == 0:
            return None  # instrument buisy or no data found

        status = data[0]  # P = data valid
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

        self.range = self._range[data[1]]
        self.mode = self._mode[data[2]]

        reading = float(data[3:8])
        if data[3] != ' ':  # white space = positive, else negative
            reading = -reading
        exponent = -int(data[10:12])
        reading = reading * 10 ** exponent

        if all_data:
            return {
                'range': self.range,
                'mode': self.mode,
                'reading': reading,
            }
        else:
            return reading

    def autozero(self):
        """perform autozero on probe, no RF power must be applied"""
        self._write('Z')

    def enable_cal_factor(self, enable=True):
        """enable or disable front panel cal factor knob"""
        if enable:
            self._write('-')
            self.cal_factor_enabled = True
        else:
            self._write('+')
            self.cal_factor_enabled = False

    def set_measurement_rate(self, rate: str):
        """set the measurement rate, avaiable:\n
        -> 'hold' : the power meter is set in HOLD (no read, no data output) until a trigger is received\n
        -> 'free_run_fast' : make continuous measurements and output data with no setlling time\n
        -> 'free_run' : make continuous measurements and output data with no setlling time"""
        if rate in self._measurement_rate:
            self._write(self._measurement_rate[rate])
        else:
            raise Exception('invalid measurement rate')

    def trigger(self, settling: bool = True):
        """trigger a measurement, defaulkt with settling else use optional argument 'settling' to disable"""
        if settling:
            # 'trigger_settling' : make une measurement and output data with settling tie, HOLD until next trigger
            self._write(self._measurement_rate['trigger_settling'])
        else:
            # 'trigger_immediate' : make une measurement and output data as fast as possible with no settling time, HOLD until next trigger
            self._write(self._measurement_rate['trigger_immediate'])


meter = HP436A(interface, 13)


meter.cal_factor_enabled(False)

while True:
    try:
        print(meter.read(all_data=True), end='\r')
    except meter.OverRange:
        print('WARNING : power too high!', end='\r')
    except meter.UnderRange:
        print('under range', end='\r')
    except meter.AutoZeroInProgress:
        print('meter is performing autozero, please wait', end='\r')
    except meter.AutoZeroOverRange:
        print('WARNING : error performing probe autozero', end='\r')
    sleep(0.5)
