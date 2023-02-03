class HP3478A:
    from PyAR488.PyAR488 import AR488

    _function = {
        'DCV': 'F1',
        'ACV': 'F2',
        '2W_OHM': 'F3',
        '4W_OHM': 'F4',
        'DCI': 'F5',
        'ACI': 'F6',
        'EXT_OHM': 'F7'
    }

    # todo  : range

    _digits = {
        '3.5': 'N3',
        '4.5': 'N4',
        '5.5': 'N5',
    }

    _trigger = {
        'INTERNAL': 'T1',
        'EXTERNAL': 'T2',
        'SINGLE': 'T3',
        'HOLD': 'T4',
        'FAST': 'T5'
    }

    def __init__(self, interface: AR488, address:int, name='HP3577A'):
        self.address = address
        self.interface = interface
        self.name = name

    def _write(self, command):
        self.interface.address(self.address)
        self.interface.bus_write(command)

    def read(self):
        self.interface.address(self.address)
        return float(self.interface.read())

    def query(self, command, payload=False, decode=True):
        self.interface.address(self.address)
        return self.interface.query(command, payload=payload, decode=decode)

    # ------------------------------------------------------------------------------------
    def read_error_register(self):
        error_reg = self.query('E', payload=True)
        error_reg_bin = format(error_reg, 'b')
        error_bits = [True if i == '1' else False for i in error_reg_bin]
        error_log = []
        if error_bits[0]:
            error_log.append('0: incorrect cal ram checksum or range checksum error')
        if error_bits[1]:
            error_log.append('1:Main CPU RAM self-test failed')
        if error_bits[2]:
            error_log.append('Control ROM self test failed')
        if error_bits[3]:
            error_log.append('A/D slope error detected')
        if error_bits[4]:
            error_log.append('A/D self test failed')
        if error_bits[5]:
            error_log.append('A/D link fail (between U403 and U462')
        return error_log

    def get_status(self):
        """
        1: Functon, Range, Number of digits
        2: Instrument status,
        3: SRQ mask
        4: Internal error info
        5: ADC value"""
        status_bytes = self.query('B')
        status_bytes = [status_bytes[i:i + 2] for i in range(0, len(status_bytes))]  # to be tested
        data = []
        for i in range(len(status_bytes)):
            data.append(f'{i}:{str(data[i])}')
        return data

    def enable_srq_button(self, send: bool = True):
        """for button enable bit 4 of SRQ mask must be set or returns the formatted command string"""
        command_string = 'M20'
        if send:
            self._write(command_string)
        else:
            return command_string

    def enable_srq_data_ready(self, send: bool = True):
        """set bit 0 of SRQ mask, remains set until spoll or returns the formatted command string"""
        command_string = 'M01'
        if send:
            self._write(command_string)
        else:
            return command_string

    def get_front_rear_switch_state(self):
        """returns the selected input 'FRONT' or 'REAR'"""
        val = self.query('S', payload=True)
        if val == '1':
            return 'FRONT'
        elif val == '0':
            return 'REAR'
        else:
            raise Exception('invalid response')

    def print_text(self, text: str, send: bool = True):
        """prints an uppercase text on display or returns the formatted command string,
        the text remains for 10 minutes than blank, normal display by D1 command, CLEAR or error"""
        text = text.upper()
        if len(text) > 12:
            text = text[:12]
        command_string = f'D2{text}'
        if send:
            self._write(command_string)  # D3 is same but do not update annunciators
        else:
            return command_string

    def normal_display(self, send: bool = True):
        """switch to normal reading display or returns the formatted command string"""
        command_string = 'D1'
        if send:
            self._write(command_string)
        else:
            return command_string

    def clear_status_register(self, send: bool = True):
        """switch to normal reading display or returns the formatted command string"""
        command_string = 'K'
        if send:
            self._write(command_string)
        else:
            return command_string

    def get_status_byte(self, mode='int'):
        """returns the status byte of the instrument as an int or a dict"""
        response = self.interface.prologix_spoll(self.address)
        try:
            response = int(response)
        except ValueError:
            return None

        if mode == 'int':
            return int(response)
        elif mode == 'dict':
            response_bits = format(response, 'b')
            while len(response_bits) < 8:
                response_bits += '0'
            status_byte_dict = {
                'Data_ready': True if response_bits[0] == '1' else False,
                'Syntax_error': True if response_bits[2] == '1' else False,
                'Internal_error': True if response_bits[3] == '1' else False,
                'Front_SRQ': True if response_bits[4] == '1' else False,
                'Invalid_cal': True if response_bits[5] == '1' else False,
                'SRQ': True if response_bits[6] == '1' else False,
                'Power_on_SRQ': True if response_bits[7] == '1' else False
            }
            return status_byte_dict
        else:
            raise Exception('invalid mode')

    def set_function(self, function: str, send: bool = True):
        """sets the measurement function or returns the formatted command string,
        available : 'DCV','ACV','2W_OHM','4W_OHM','DCI','ACI','EXT_OHM'"""
        if function in self._function.keys():
            command_string = self._function[function]
            if send:
                self._write(command_string)
            else:
                return command_string
        else:
            raise Exception('invalid function')

    def set_trigger(self, trigger:str, send: bool = True):
        """sets the trigger or returns the formatted command string,
        available : 'INTERNAL','EXTERNAL','SINGLE','HOLD','FAST'"""
        if trigger in self._trigger.keys():
            command_string = self._trigger[trigger]
            if send:
                self._write(command_string)
            else:
                return command_string
        else:
            raise Exception('invalid trigger')

    def enable_auto_zero(self, send: bool = True):
        """enable auto zero function or returns the formatted command string"""
        command_string = 'Z1'
        if send:
            self._write(command_string)
        else:
            return command_string

    def disable_auto_zero(self, send: bool = True):
        """disable auto zero function or returns the formatted command string"""
        command_string = 'Z0'
        if send:
            self._write(command_string)
        else:
            return command_string

    def enable_auto_range(self, send: bool = True):
        """enable auto range or returns the formatted command string"""
        command_string = 0
        if send:
            self.interface.write(command_string)
        else:
            return command_string

    def set_digits(self, new_digits, send: bool = True):
        """sets or returns the formatted command string,
        available : '3.5','4.5','5.5'"""
        if new_digits in self._digits.keys():
            command_string = self._digits[new_digits]
            if send:
                self.interface.write(command_string)
            else:
                return command_string
        else:
            raise Exception('invalid digits')

    def push(self, *args):
        """list of tuples arranged as (function, argument) and packs all programming codes to in a single command,
        use to optimize instrument settling time"""
        if len(args) > 0:
            command_string = ''
            for i in args:
                # i = (function, argument)
                command_string += i[0](i[1], send=False)
            self._write(command_string)
