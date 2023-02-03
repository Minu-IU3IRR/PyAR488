
class RF_plugin:
    def __init__(self, frequency_range, output_level_range) -> None:
        self.frequency_range = frequency_range
        self.output_level_range = output_level_range

class MOD_plugin:
    def __init__(self, *capabilities) -> None:
        self.capabilities = capabilities


# 0.01MHz -> 110MHz, 200kHz with some specification degradation
RF_86601A = RF_plugin(frequency_range=(
    0.01 * 10 ** 6, 109.999999 * 10**6), output_level_range=(+13.0, -146.0))

# 1MHz -> 2.6GHz, 200kHz with some specification degradation
RF_86603A = RF_plugin(frequency_range=(
    200 * 10**3, 2599.999998 * 10**6), output_level_range=(+10.0, -136.0))

#AM, FM plugin
MOD_36633B = MOD_plugin('AM', 'FM')


class HP8660D:
    """HP 8660D RF frequency generator with plugins"""

    from PyAR488.PyAR488 import AR488

    _sweep_rate = {
        'slow': 'T1',
        'medium': 'T2',
        'fast': 'T3'
    }

    def __init__(self, interface: AR488, address, modulation_plugin:MOD_plugin=None, rf_plugin:RF_plugin=None) -> None:
        self.interface = interface
        self.address = address
        self.modulation_plugin = modulation_plugin
        self.rf_plugin = rf_plugin
        self.hpib_new_mode()  # configure the correct command set

    # internals
    def _write(self, message: str):
        """internal function to send a message on the GPIB bus.
        Since the interface must be on the same address of the instrument, every time a write function in called the address is checked by the AR488 and if different changed to the correct one"""
        self.interface.address(self.address)
        self.interface.bus_write(message)

    # FREQUENCY
    def center_frequency(self, new_freq: int):
        """set the center frequency of the seweep or CW operation"""
        if self.rf_plugin is not None:
            if not self.rf_plugin.frequency_range[0] <= new_freq <= self.rf_plugin.frequency_range[1]:
                raise Exception('frequency outside plugin capability')
        self._write(f'FR{new_freq}HZ')

    def frequency_step_up(self):
        """increase the frequency by the setted increment value"""
        self._write(f'UP')

    def frequency_step_down(self):
        """decrease the frequency by the setted increment value"""
        self._write(f'DN')

    def frequency_increment(self, new_freq_step: float):
        """ set frequency step value for frequency_step_up and down functions"""
        self._write(f'FR{new_freq_step}HZ')

    # AMPLITUDE
    def output_level(self, level: float):
        """set output level in dBm (50ohm)"""
        if self.rf_plugin is not None:
            if not self.rf_plugin.output_level_range[0] <= level <= self.rf_plugin.output_level_range[1]:
                raise Exception('output level outside plugin capability')

        if level >= 0:
            unit = '+dm'
        else:
            unit = '-dm'
        self._write(f'AP{abs(level)}' + unit)

    # MODULATION
    def fm_deviation(self, deviation: float):
        """set FM modulation deviation in HZ, resolution limited to 3 digits"""
        if self.modulation_plugin is not None:
            if not 'FM' in self.modulation_plugin.capability:
                raise Exception(
                    'FM modulation not available in current plugin')

        dev_str = str(deviation)
        if len(dev_str) > 3:
            dev_str = dev_str[:3]
        self._write('FM' + dev_str + 'HZ')

    def am_depth(self, depth: float):
        """AM modulation depth in absolute value (0->1.0)"""
        if self.modulation_plugin is not None:
            if not 'AM' in self.modulation_plugin.capability:
                raise Exception(
                    'AM modulation not available in current plugin')

        if 0 <= depth <= 1.0:
            perc = int(100.0 * depth)
            self._write(f'AM{perc}PC')
        else:
            raise Exception(
                f'modulation depth out of range (0->1.0), given {depth}')

    def phase_modulation(self, deviation: int):
        """phase modulztion deviation in DEG (0-360)"""
        if self.modulation_plugin is not None:
            if not 'PM' in self.modulation_plugin.capability:
                raise Exception(
                    'PHASE modulation not available in current plugin')

        if 0 <= deviation <= 360:
            if deviation == 360:
                deviation = 0
            self._write(f'PM{deviation}DG')
        else:
            raise Exception(
                f'phase modulation angle out of range(0->360), given {deviation}')

    # todo
    def modulation_off(self):
        """not yet implemented"""
        self._write('MO')

    # todo
    def modulation_level(self):
        """not yet implemented"""
        pass

    # todo
    def fm_calibration(self):
        """not yet implemented"""
        pass

    # todo
    def modulation_degrees(self):
        """not yet implemented"""
        pass

    # DISPLAY
    # display black and display output in same function
    def enable_display(self, state: bool = True):
        """enable or disable display, usage:
        -enable_display() or enabl_display(True) -> enable the display
        -enabledisplay(False) -> disable display"""
        if state:
            self._write('DB')
        else:
            self.write('DO')

    # MISC
    def hpib_old_mode(self):
        self._write('OLD')

    def hpib_new_mode(self):
        self._write('NEW')

    def register_clear(self):
        self._write('/')

    # MODULATION SOURCE
    def internal_1kHz(self):
        self._write('M1')

    def internal_400Hz(self):
        self._write('M2')

    def internal_dc_couple(self):
        self._write('M4')

    def internal_ac_couple(self):
        self._write('M8')

    def internal_ac_unleveled(self):
        self._write('M9')

    # SWEEP
    def sweep_width(self, width: float):
        """sets sweep width in Hz"""
        if width > 0:
            self._write(f'FS{width}HZ')
        else:
            raise Exception('sweep width < 0')

    def sweep_off(self):
        """disable sweep"""
        self._write('WO')

    def sweep_auto(self):
        """continuous sweep"""
        self._write('W1')

    def sweep_single(self):
        """single sweep, starts when sweep_trigger() is called """
        self._write('W2')

    def sweep_trigger(self):
        """used to trigger the single sweep start"""
        self._write('W3')

    def sweep_rate(self, rate=1):  # dedicated class
        """define sewwp rate, can be used in two ways:
        string : slow, medium or fast
        int : 0, 1, 2 representing the string index of the stiring list"""
        if type(rate) == int:
            try:
                rate = self._sweep_rate[self._sweep_rate.keys()[rate]]
            except:
                raise Exception('invalid sweep rate defined by int value')
        elif type(rate) == str:
            try:
                rate = self._sweep_rate[rate]
            except:
                raise Exception('invalid sweep rate defined by string value')
        else:
            raise Exception('invalid definition of sweep mode')
        self._write(rate)

    # abstractions
    def source(self, frequency: int, level: float):
        """quick function so set output freqeuncy [Hz] and level [dBm] in one function"""
        self.center_frequency(frequency)
        self.output_level(level)

    def sweep(self, start: int, stop: int, rate):
        """quick function so set a sweep from start[Hz], stop[Hz] and speed.
        speed : as in sweep_rate use string ('slow', 'medium', 'fast') or int (1,2,3)
        WARNING : make sure that center frequency is an integer and not xx.5, if case will be sounded to next integer"""
        width = stop - start
        center = start + width/2
        self.center_frequency(center)
        self.sweep_width(width)
        self.sweep_rate(rate)

    def modulation(self, type:str, source:str, parameter):
        """quick function so detup a modulation, 
         type   - source           - parameter:                                                   
         'AM'   |  'int' or 'ext'  |   depth (0->1.0) = 0->100%
         'FM'   |  'int' or 'ext'  |   deviation (xxxHz), with resolution constrained to 3 digits,
         'PM'   |  'int' or 'ext'  |   still to be implemented
         if source is internal it defaults to 1KHz"""
        self.internal_1kHz()
        if type == 'AM':
            self.am_depth(parameter)
        elif type == 'FM':
            self.fm_deviation(parameter)
        elif type == 'PM':
            raise Exception('phase modulation not yet implemented!')
        else:
            raise Exception('invlaid modulation mode')
