def _format_numeric(val: float):
    if type(val) == int:
        val = float(val)
    return f'{val:.5}'

class HP8903A:
    """ module for controlling HP8903A from AR488 GPIb to USB adapter
        written by : Manuel Minutello"""

    from PyAR488.PyAR488 import AR488
    from time import sleep

    _measurements = {
        'AC': 'M1',
        'SINAD': 'M2',
        'DISTORTION': 'M3',
        'DC': 'S1',
        'SNR': 'S2',
        'DISTORTION_LEVEL': 'S3'
    }
    _HP_filters = {  # H*  -> H0 = off
        '400Hz': 1,
        'PSOPH': 2
    }
    _LP_filters = {  # L*  -> L0 = off
        '30kHz': 1,
        '80kHz': 2
    }
    _trigger_mode = {
        'FREE_RUN': 'T0',
        'HOLD': 'T1',
        'INTERMEDIATE': 'T2',  # WARNING : see 3-27 of manual, wrong result may appear!!!
        'SETTLING': 'T3'
    }
    _settling_times = {  # time needed by the instruemnt to receive the message
        'spoll': 1,  # tested
        'measurement': 1,
        'source': 1,  # testing
        'general': 1,
        'trigger': 1,
        'filter': 1,
        'scale': 1,
        'special': 2,
        'display': 1,
        'clear': 1,
        'automatic': 1
    }
    _valid_screens = ('RL', 'RR', 'LEFT', 'RIGHT', 'FREQUENCY', 'MEASUREMENT')

    def __init__(self, interface: AR488,address:int, name='HP8903A'):
        self.address = address
        self.interface = interface
        self.name = name

        self.send_special_function('41.0')  # preset

        self.source_start_frequency = 20
        self.source_stop_frequency = 20000
        self.plot_limit_low = -100.0  # todo
        self.plot_limit_high = +100.0  # todo
        self.xy_recorder_enable = True  # todo
        self.source_frequency = 1000.0
        self.frequency_increment = 1000.0
        self.source_amplitude = 0.00
        self.source_amplitude_increment = 0.100
        self.measurement = 'AC'
        self.LP_active_filters = ['80kHz']
        self.HP_active_filters = []
        self.special_functions = []
        self.ratio_enabled = False
        self.lin_log_measurement = 'lin'
        self.selected_display = 'RR'
        self.trigger_mode = 'T0'
        self.sweep_enable = False

        self.srq_enabled = False

    # exceptions
    class InstrumentError(Exception):
        def __init__(self, message):
            super().__init__(message)

    class ReadError(Exception):
        def __init__(self, message):
            super().__init__(message)

    class GpibError(Exception):
        def __init__(self, message):
            super().__init__(message)

    # internal commands
    def _write(self, command):
        self.interface.address(self.address)  # interface checks if send or already set
        self.interface.bus_write(f'{command}')

    def read(self, mode='float'):
        self.interface.address(self.address)
        response:str = self.interface.read()

        if response == b'E-04\r\n':
            response = self.interface.read()
            if response == b'E-04\r\n':
                raise self.ReadError(f'invalid reading {response}')

        if response.startswith(b'+900') and response.endswith(b'E+05\r\n'):
            raise self.InstrumentError(f'Instrument error {int(response[4:6])}')  # todo : error description

        if mode == 'float':
            try:
                return float(response)
            except ValueError:
                raise self.ReadError(f'invalid value {response}')
        elif mode == 'text':
            return response
        else:
            raise Exception('invalid repsonse query')

    # ----------------------
    def get_status_byte(self, mode='int'):
        response = self.interface.spoll(self.address)
        self.sleep(self._settling_times['spoll'])
        try:
            status_byte_int = int(response)
        except ValueError:
            return None

        status_bits_string = format(status_byte_int, 'b')
        while len(status_bits_string) < 8:
            status_bits_string += '0'
        status_byte_dict = {
            'data_ready': True if status_bits_string[0] == '1' else False,
            'HPIB_error': True if status_bits_string[1] == '1' else False,
            'instrument_error': True if status_bits_string[2] == '1' else False,
            'SRQ': True if status_bits_string[6] == '1' else False,
        }

        if status_byte_dict['instrument_error']:  # todo : doesn't work, spoll response = error code
            error = self.read()
            raise Warning(f'Instruemnt Error:{error}')
        elif status_byte_dict['HPIB_error']:
            error = self.read()
            raise Warning(f'HPIB Error:{error}')

        if mode == 'int':
            return status_byte_int
        if mode == 'dict':
            return status_byte_dict

    # ---------------------------------------
    def set_source_start_frequency(self, new_value, send: bool = True, update: bool = True):
        """sets signal source sweep start frequency in Hz or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        formatted_value_string = _format_numeric(new_value)
        if formatted_value_string != str(self.source_start_frequency):  # send only if value is changed
            command_string = f'FA{formatted_value_string}HZ'
            if update:
                self.source_start_frequency = float(formatted_value_string)  # store as string to use outside
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    def set_source_stop_frequency(self, new_value, send: bool = True, update: bool = True):
        """sets signal source sweep stop frequency in Hz or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        formatted_value_string = _format_numeric(new_value)
        if formatted_value_string != str(self.source_stop_frequency):  # send only if value is changed
            command_string = f'FB{formatted_value_string}HZ'
            if update:
                self.source_stop_frequency = float(formatted_value_string)  # store as string to use outside
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    # todo : plot limit,

    def set_source_frequency(self, new_value, send: bool = True, update: bool = True):
        """sets signal source frequency in Hz or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        formatted_value_string = _format_numeric(new_value)
        if formatted_value_string != str(self.source_frequency):  # send only if value is changed
            command_string = f'FR{formatted_value_string}HZ'
            if update:
                self.source_frequency = float(formatted_value_string)
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            return ''  # return empty string to represent no command necessary

    def set_source_frequency_increment(self, new_value, send: bool = True, update: bool = True):
        """sets signal source frequency increment (button action) in Hz or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        formatted_value_string = _format_numeric(new_value)
        if formatted_value_string != str(self.frequency_increment):  # send only if value is changed
            command_string = f'FN{formatted_value_string}HZ'
            if update:
                self.frequency_increment = float(formatted_value_string)  # store as string to use outside
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    def set_source_amplitude(self, new_value, send: bool = True, update: bool = True):
        """sets signal source amplitude in Volts rms or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        formatted_value_string = _format_numeric(new_value)
        if formatted_value_string != str(self.source_amplitude):  # send only if value is changed
            command_string = f'AP{formatted_value_string}VL'
            if update:
                self.source_amplitude = float(formatted_value_string)  # store as string to use outside
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    def set_source_amplitude_increment(self, new_value, send: bool = True, update: bool = False):
        """sets signal source amplitude increment (button action) in Volts rms or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        formatted_value_string = _format_numeric(new_value)
        if formatted_value_string != self.source_amplitude_increment:  # send only if value is changed
            command_string = f'AN{formatted_value_string}VL'
            if update:
                self.source_amplitude_increment = float(formatted_value_string)  # store as string to use outside
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    def clear(self, send=True):
        """sends Clear command or returns the formatted command string"""  # todo : clears status byte?
        command_string = 'CL'
        if send:
            self._write(command_string)
            self.sleep(self._settling_times['general'])
        else:
            return command_string

    def set_sweep_state(self, new_enable_state: bool = True, send: bool = True, update: bool = True):
        """enabled/disables the source sweep function or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if self.sweep_enable != new_enable_state:  # send only if value is changed
            command_string = f'W{1 if new_enable_state else 0}'
            if update:
                self.sweep_enable = new_enable_state
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['source'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    # todo  step_up, step_down

    def automatic_operation(self, send: bool = True):
        """sends Automatic Operation command or returns the formatted command string"""
        command_string = 'AU'
        if send:
            self._write(command_string)
            self.sleep(self._settling_times['automatic'])
        else:
            return command_string

    def set_measurement(self, new_measurement: str, send: bool = True, update: bool = True):
        """sets the measurement function or returns the formatted command string valid values : {},
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if new_measurement in self._measurements.keys():
            if new_measurement != self.measurement:  # send only if value is changed
                command_string = self._measurements[new_measurement]
                if update:
                    self.measurement = new_measurement
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['measurement'])
                else:
                    return command_string
            else:  # measurement unchanged
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid measurement {new_measurement}')

    def enable_hp_filter(self, filter_to_enable: str, send: bool = True, update: bool = True):
        """enable a High Pass Filter or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if filter_to_enable in self._HP_filters.keys():
            command_string = self._HP_filters[filter_to_enable]
            if filter_to_enable not in self.HP_active_filters:  # send only if value is changed
                if update:
                    self.HP_active_filters.append(filter_to_enable)
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['filters'])
                else:
                    return command_string
            else:  # measurement unchanged
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid HP filter {filter_to_enable}')

    def disable_hp_filter(self, filter_to_disable: str, send: bool = True, update: bool = True):
        """disable a High Pass Filter or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if filter_to_disable in self._HP_filters.keys():
            if filter_to_disable in self.HP_active_filters:  # send only if value is changed
                command_string = 'H0'  # disable all hp filters
                for i in self.HP_active_filters:  # restore all other active filters
                    command_string += self._HP_filters[i]

                if update:
                    self.HP_active_filters.remove(filter_to_disable)
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['filters'])
                else:
                    return command_string
            else:
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid HP filter {filter_to_disable}')

    def enable_lp_filter(self, filter_to_enable: str, send: bool = True, update: bool = True):
        """enable a Low Pass Filter or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if filter_to_enable in self._LP_filters.keys():
            command_string = self._LP_filters[filter_to_enable]
            if filter_to_enable not in self.LP_active_filters:  # send only if value is changed
                if update:
                    self.LP_active_filters.append(filter_to_enable)
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['filters'])
                else:
                    return command_string
            else:  # measurement unchanged
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid LP filter {filter_to_enable}')

    def disable_lp_filter(self, filter_to_disable: str, send: bool = True, update: bool = True):
        """disable a Low Pass Filter or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if filter_to_disable in self._LP_filters.keys():
            if filter_to_disable in self.LP_active_filters:  # send only if value is changed
                command_string = 'L0'  # disable all lp filters
                for i in self.LP_active_filters:  # restore all other active filters
                    command_string += self._LP_filters[i]

                if update:
                    self.LP_active_filters.remove(filter_to_disable)
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['filters'])
                else:
                    return command_string
            else:
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid LP filter {filter_to_disable}')

    def ratio_measurement(self, new_ratio_enable_state: bool, send: bool = True, update: bool = True):
        """enables Ratio Measurement or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if self.ratio_enabled != new_ratio_enable_state:  # send only if value is changed
            command_string = f'R{1 if new_ratio_enable_state else 0}'
            if update:
                self.ratio_enabled = new_ratio_enable_state
            if send:
                self._write(command_string)
                self.sleep(self._settling_times['scale'])
            else:
                return command_string
        else:
            if not send:
                return ''  # return empty string to represent no command necessary

    def measurement_scale(self, new_measurement_scale: str = 'lin', send: bool = True, update: bool = True):
        """sets measurement scale ("lin"/"log") or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if new_measurement_scale in ('lin', 'log'):
            if self.lin_log_measurement != new_measurement_scale:  # send only if value is changed
                command_string = 'LN' if new_measurement_scale == 'lin' else 'LG'
                if update:
                    self.lin_log_measurement = new_measurement_scale
                if send:
                    self._write(command_string)
                    self.lin_log_measurement = new_measurement_scale
                else:
                    return command_string
            else:
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid measurement scale {new_measurement_scale}')

    def set_trigger(self, new_trigger, send: bool = True, update: bool = True):  # toReview
        """sets Instrument Trigger mode or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if new_trigger in self._trigger_mode.keys():
            if new_trigger != self.trigger_mode:  # send only if value is changed
                command_string = self._trigger_mode[new_trigger]
                if update:
                    self.trigger_mode = new_trigger
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['trigger'])
                else:
                    return command_string
            else:
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid trigger mode {new_trigger}')

    def set_read_display(self, new_screen: str, send: bool = True, update: bool = True):
        """selects the display that responds to a read command or returns the formatted command string,
        WARNING:updates the local frequency variable if "update" field is not configured as False"""
        if new_screen in self._valid_screens:
            if new_screen == 'FREQUENCY' or new_screen == 'LEFT' or new_screen == 'RL':
                command_string = 'RL'
            else:
                command_string = 'RR'

            if command_string != self.selected_display:  # send only if value is changed
                if update:
                    self.selected_display = command_string  # store as command RL or RR for simplicity
                if send:
                    self._write(command_string)
                    self.sleep(self._settling_times['display'])
                else:
                    return command_string
            else:
                if not send:
                    return ''  # return empty string to represent no command necessary
        else:
            raise Exception(f'invalid display {new_screen}')

    # todo : rapid frequency count
    # todo : rapid_source

    def send_special_function(self, function, send: bool = True):
        """sends a special function (xx.y) or returns the formatted command string"""
        # todo : if special  == preset -> preset local settings
        command_string = f'{function}SP'
        if send:
            self._write(command_string)
            self.sleep(self._settling_times['special'])
        else:
            return ''  # return empty string to represent no command necessary

    def enable_srq(self, config=None, send=True, update: bool = True):  # toReview
        """sets SRQ level, sun wanted values :
                1 = Data ready
                2 = HP-IB error
                4 = Instrument error
        or returns the formatted command string"""

        if config is None:
            config = {'data_ready': False, 'HPIB_error': False, 'instrument_error': False}

        new_level = 0
        if 'data_ready' in config.keys() and config['data_ready']:
            new_level += 1
        if 'HPIB_error' in config.keys() and config['HPIB_error']:
            new_level += 2
        if 'instrument_error' in config.keys() and config['instrument_error']:
            new_level += 4

        command_string = f'22.{new_level}SP'  # special function
        if update and new_level >= 1:
            self.srq_enabled = True
        if send:
            self._write(command_string)
            self.sleep(self._settling_times['special'])
        else:
            if not send:
                return command_string

    # ---------------------------------------------------------
    # custom functions

    def await_measurement(self, mode='DR'):
        """wait for measurement complete, modes :
        -DR : data ready
        -DR+SRQ : data + service request (enable SRQ required)"""
        if not self.srq_enabled:
            raise Exception('function require SRQ events to be active in data ready condition, use enable_srq()')

        while True:
            if self.interface.prologix_read_srq():
                status_byte = self.get_status_byte('dict')

                # error check
                if status_byte is not None:
                    if status_byte['HPIB_error']:
                        raise self.GpibError('instrument reported HPIB error')
                    if status_byte['instrument_error']:
                        raise self.InstrumentError(self.read())

                if mode == 'DR':
                    if status_byte is not None and status_byte['data_ready']:
                        break
                elif mode == 'DR+SRQ':
                    if status_byte is not None and status_byte['data_ready'] and status_byte['SRQ']:
                        break
                else:
                    raise Exception('invalid response wait method')

    def read_frequency_display(self):
        """returns the reading of the measurement display without permanently setting it to the default read target"""
        old_display = self.selected_display
        self.set_read_display('FREQUENCY')
        meas = self.read()
        self.set_read_display(old_display)
        return meas

    def read_measurement_display(self):
        """returns the reading of the measurement display without permanently setting it to the default read target"""
        old_display = self.selected_display
        self.set_read_display('MEASUREMENT')
        meas = self.read()
        self.set_read_display(old_display)
        return meas

    def push(self, *args):
        """list of tuples arranged as (function, argument) or ...,function,.... and packs all programming codes to in a single command,
        use to optimize instrument settling time"""
        if len(args) > 0:
            command_string = ''
            for i in args:
                # i = (function, argument)
                if type(i) == tuple:
                    command_string += i[0](i[1], send=False)
                else:
                    command_string += i(send=False)  # function with no arguments
            self._write(command_string)