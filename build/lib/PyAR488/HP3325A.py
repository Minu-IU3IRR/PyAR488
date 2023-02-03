
def _constrain_com_len(val, limit):
        val_str = str(val)
        error = False
        if val > 0:
            if len(val_str) > limit:
                val_str = val_str[:limit]
                error = True
        else:
            if len(val_str) > limit + 1:
                val_str = val_str[:limit + 1]
                error = True
        if error:
            pass
        return val_str


class HP3325A:
    """ module for controlling HP3325A from AR488 GPIb to USB adapter
    written by : Manuel Minutello

    ->  use the functions to set up and read back the instrument"""
    # GPIB command on page 43 of manal

    from PyAR488.PyAR488 import AR488
    _function = {
        'DC': '0',
        'sine': '1',
        'square': '2',
        'triangle': '3',
        'ramp_positive': '4',
        'ramp_negative': '5'
    }

    _sweep_mode = {
        'lin': '1',
        'log': '2'
    }

    _amplitude_units = {
        'V': 'VO',
        'mV': 'MV',
        'V_RMS': 'VR',
        'mV_RMS': 'MR',
        'dBm': 'DB'
    }

    _offset_units = {
        'V': 'VO',
        'mV': 'MV',
    }

    from time import sleep
    def __init__(self, interface:AR488, address, name='HP478A'):
        self.address = address
        self.interface = interface
        self.name = name

    def _write(self,command:str):
        """internal function that changes the interface address before writing on bus"""
        self.interface.address(self.address)
        self.interface.bus_write(command)

    def _query(self,command, payload = False, decode = True):
        """internal function that changes the interface address before query on bus"""
        self.interface.address(self.address)
        self.interface.query(command,payload,decode)

    def clear(self):
        """clear instrument"""
        self._write('DCI')  # todo : test

    # commands
    def set_function(self, func):
        """sets the generator function : 
        'DC','sine', 'square', 'triangle', 'ramp_positive', 'ramp_negative'"""
        if func in self._function.keys():
            self._write(f'FU{self._function[func]}')
        else:
            raise Exception(f'invalid mode "{func}"')

    def set_frequency(self, freq: float):
        """set output frequency in Hz, pay attension to the maximum frequency in each range"""
        freq_str = _constrain_com_len(freq, 11, 'frequency')
        self._write(f'FR {freq_str} HZ')  # also KH or MH valid
        # 7.0 ms for freq setting + 12.5ms for range selection
        self.sleep(0.02)

    def set_amplitude(self, amp: float, unit: str = _amplitude_units['V']):
        """set output voltage (50ohm), default unit is Volt. use _amplitude_units[X] to chose other units like: 'V','mV','V_RMS','mV_RMS','dBm'"""
        if unit not in self._amplitude_units.keys():
            raise Exception(f'invalid amplitude unit "{unit}"')

        amp_str = _constrain_com_len(amp, 4)
        self._write(f'AM {amp_str} {self._amplitude_units[unit]}')

    def set_offset(self, offset: float, unit: str):
        """set output DC offset, default unit is Volt. use _amplitude_units[X] to chose other units like: 'V','mV','V_RMS','mV_RMS','dBm'"""
        if unit not in self._offset_units.keys():
            raise Exception(f'invalid offset unit "{unit}"')

        offset_str = _constrain_com_len(offset, 4)
        self._write(f'OF {offset_str} {self._offset_units[unit]}')

    def set_phase(self, phase: float):  # unit = deg
        """set output phase respect to sync signal, unit is DEG (0-359°)"""
        phase_str = _constrain_com_len(phase, 4)
        self._write(f'PH {phase_str} DE')

    def set_frequency_sweep(self, start_freq: float, stop_freq: float):
        """quick functon so set up a frequenyc sweep with START and STOP values in Hz"""
        start_freq_str = _constrain_com_len(start_freq, 11)
        self._write(f'ST {start_freq_str} HZ')  # also KH or MH valid

        stop_freq_str = _constrain_com_len(stop_freq, 11)
        self._write(f'SP {stop_freq_str} HZ')  # also KH or MH valid

    def set_marker_frequency(self, freq):
        """set marker frequency in Hz"""
        marker_str = _constrain_com_len(freq, 11)
        self._write(f'MF {marker_str} HZ')  # also KH or MH valid

    def set_sweep_time(self, time):
        """set sweep time in s"""
        time_str = _constrain_com_len(time, 4)
        self._write(f'TI {time_str} SE')

    def set_sweep_mode(self, mode: str):
        """set swppe mode, use 'lin' or 'log'"""
        if mode not in self._sweep_mode.keys():
            raise Exception(f'invalid sweep mode "{mode}"')
        
        self._write(f'SM {self._sweep_mode[mode]}')

    def enable_front_panel_output(self):
        """pass the signal output to front panel connector"""
        self._write('RF1')

    def enable_rear_panel_output(self):
        """pass the signal output to rear panel connector"""
        self._write('RF2')

    def store_program(self, reg: int):
        if 0 <= reg <= 9:
            self._write(f'SR {reg}')

    def recall_program(self, reg: int):
        if 0 <= reg <= 9:
            self._write(f'RE {reg}')

    def set_phase_zero(self):
        """set phase offset to zero"""
        self._write('AP')

    def auto_cal(self):
        """perform auto calibration"""
        self._write('AC')

    def start_single_sweep(self):
        """trigger the start of sweep"""
        self._write('SS')

    def start_continuous_sweep(self):
        """trigger the continuous sweep"""
        self._write('SC')

    def self_test(self):
        """perform self test"""
        self._write('TE')

    def get_program_error(self):
        """interrogte instrument to get the program error"""
        return self._query('IER', payload=True)

    def get_frequency(self):
        """interrogate instrument abount current setted frequency"""
        return self._query('IFR', payload=True)

    def get_amplitude(self):
        """interrogate instrument abount current setted amplitude"""
        return self._query('IAM', payload=True)

    def get_offset(self):
        """interrogate instrument abount current setted offset"""
        return self._query('IOF', payload=True)

    def get_phase(self):
        """interrogate instrument abount current setted phase"""
        return self._query('IPH', payload=True)

    def get_sweep_range(self):
        """interrogate instrument abount current setted sweep range"""
        start = self._query('IST', payload=True)
        stop = self._query('ISP', payload=True)
        return start, stop

    def get_marker_freq(self):
        """interrogate instrument abount current setted marker frequency"""
        return self._query('IMF', payload=True)

    def get_sweep_time(self):
        """interrogate instrument abount current setted sweep time"""
        return self._query('ITI', payload=True)

    def current_function(self):
        """interrogate instrument abount current setted wave function"""
        return self._query('IFU', payload=True)

    def enable_hv_output(self, state=True):
        """enable high voltage output option"""
        self._write(f'HV {1 if state else 0}')

    def enable_am(self, state=True):
        """enable AM modulation"""
        self._write(f'MA {1 if state else 0}')

    def enable_pm(self, state=True):
        """enable PM modulation"""
        self._write(f'MP {1 if state else 0}')
