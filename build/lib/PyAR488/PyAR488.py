
class AR488:
    """Class to easily comunicate with an AR488 USB-GPIB adapter.
    For details see: https://github.com/Twilight-Logic/AR488
    -> implemented by Minu
    """

    import serial
    import time

    _valid_mode = ['device', 'controller']
    _valid_eor = ['\r\n', '\r', '\n', None, '\n\r', '\x03', '\r\n\x03', 'EOI']
    _valid_eos = ['\r\n', '\r', '\n', None]

    def __init__(self, port:str, baud:int=115200, timeout:int=1, debug:bool=False):
        try:
            self._ser = self.serial.Serial(
                port=port, baudrate=baud, timeout=timeout)
            self.time.sleep(2)  # await for serial interface open
        except Exception as e:
            raise Exception("error opening serial port {}".format(e))

        self._debug_messages = False  # do not show initial config transactions

        self._address = 1  #
        self._mode = 'controller'  #
        self._eoi = True  #
        self._eos = '\r\n'  #
        self._eot = True  #
        self._eot_char = ''  #
        self._eor = '\r\n'  #
        self._idn = '0\r\n'  #

        self.update_config()  # needed to check eos

        self._debug_messages = debug

    def update_config(self):
        self._address = int(self.address())  
        self._mode = self.mode()  
        self._eoi = self.eoi()  
        self._eos = self.eos()  
        self._eot = self.eot()  
        self._eot_char = self.eot_char()  
        self._eor = self.eor()  
        self._idn = self.idn()  

    def __del__(self):
        self._ser.close()

    def close(self):
        self.__del__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._ser.close()

    # bus commands
    def bus_write(self, message:str):
        """write a message on bus"""
        self._ser.write("{}\n\r".format(message).encode("ASCII"))
        if self._debug_messages:  # debug
            print(f'AR488 -> write :{message}')

    def bus_read(self, decode:bool=True):
        """Read from GPIB bus, decode if specified"""
        val = self._ser.readline()
        if val == b'Unrecognized command\r\n':
            raise Exception('Unrecognized command')
        if decode:
            val = val.decode('utf-8')

        if self._debug_messages:  # debug
            print(f'AR488 -> read :{val}')
        return val

    def query(self, message:str, payload:bool=False, decode:bool=True):
        """Write message to GPIB bus and read results, if a payload is expected send '++read' too,
        decode by default un UTF-8"""
        self.bus_write(message)
        if payload:
            return self.read(decode=decode)
        return self.bus_read(decode=decode)

    # Prologix commands
    def address(self, new_address: int = None, force: bool = False):
        """This is used to set or query the GPIB address. At present, only primary addresses are supported. In
        controller mode, the address refers to the GPIB address of the instrument that the operator
        desires to communicate with. The address of the controller is 0. In device mode, the address
        represents the address of the interface which is now acting as a device.
        ose force = True optional parameter to force a new address set"""
        if new_address is None:
            return self.query("++addr")
        else:
            if self._address != new_address or force:
                if 1 <= new_address <= 30:
                    self.bus_write(f'++addr {new_address}')
                else:
                    raise Exception(f'invalid address {new_address}')

                # check for correct execution
                self._address = int(self.address())
                if self._address != new_address:
                    raise Exception('Failed to set interface address')

    # todo : ++auto

    def clear(self):
        """This command sends a Selected Device Clear (SDC) to the currently addressed instrument. Details
        of how the instrument should respond may be found in the instrument manual"""
        self.bus_write('++clr')

    def eoi(self, new_eoi: bool = None):
        """This command enables or disables the assertion of the EOI signal. When a data message is sent in
        binary format, the CR/LF terminators cannot be differentiated from the binary data bytes. In this
        circumstance, the EOI signal can be used as a message terminator. When ATN is not asserted and
        EOI is enabled, the EOI signal will be briefly asserted to indicate the last character sent in a multibyte
        sequence. Some instruments require their command strings to be terminated with an EOI
        signal in order to properly detect the command"""
        if new_eoi is None:
            return bool(self.query('++eoi'))
        else:
            self.bus_write(f'++eoi {"1" if new_eoi else "0"}')

            # check
            self._eoi = self.eoi()
            if self._eoi != new_eoi:
                raise Exception('unable to set new eoi mode')

    def eos(self, new_eos: str = None):
        """Specifies the GPIB termination character. When data from the host (e.g. a command sequence) is
        received over USB, all non-escaped LF, CR or Esc characters are removed and replaced by the GPIB
        termination character, which is appended to the data sent to the instrument. This command does
        not affect data being received from the instrument"""
        if new_eos is None:
            return self._valid_eos[int(self.query('++eos'))]
        else:
            if new_eos in self._valid_eos:
                self.bus_write(f'++eos {self._valid_eos.index(new_eos)}')
            else:
                raise Exception('invalid eor char sequence')

            # check
            self._eos = self.eos()
            if self._eos != new_eos:
                raise Exception('unable to set new eos char sequence')

    def eot(self, new_eot: bool = None):
        """This command enables or disables the appending of a user specified character to the USB output
        from the interface to the host whenever EOI is detected while reading data from the GPIB port.
        The character to send is specified using the prologix_eot_char(str) witch sends ++eot_char command"""
        if new_eot is None:
            response = self.query('++eot_enable')
            if response == '0':
                return False
            return True
        else:
            self.bus_write(f'++eot_enable {"1" if new_eot else "0"}')

            # check
            self._eot = self.eot()
            if self._eot != new_eot:
                raise Exception('unable to set new eot mode')

    def eot_char(self, new_eot_char: str = None):
        """This command specifies the character to be appended to the USB output from the interface to the
        host whenever an EOI signal is detected while reading data from the GPIB bus. The character is a
        decimal ASCII character"""
        if new_eot_char is None:
            return chr(int(self.query('++eot_char')))  # store as char
        else:
            new_eot_char = ord(new_eot_char)
            if 0 <= new_eot_char <= 256:
                self.bus_write(f'++eot_char {new_eot_char}')  # send as char
            else:
                raise Exception('invalid eot_char')

            # check
            self._eot_char = self.eot_char()
            if self._eot_char == new_eot_char:
                raise Exception('unable to set new eos char sequence')

    # todo : ++help, ++ifc, ++llo, ++loc, ++lon,

    def mode(self, new_mode=None):
        """This command configures the AR488 to serve as a controller or a device.
        In controller mode the AR488 acts as the Controller-in-Charge (CIC) on the GPIB bus, receiving
        commands terminated with CRLF over USB and sending them to the currently addressed
        instrument via the GPIB bus. The controller then passes the received data back over USB to the
        host.
        In device mode, the AR488 can act as another device on the GPIB bus. In this mode, the AR488 can
        act as a GPIB talker or listener and expects to receive commands from another controller (CIC). All
        data received by the AR488 is passed to the host via USB without buffering. All data from the host
        via USB is buffered until the AR488 is addressed by the controller to talk.
        At this point the AR488 sends the buffered data to the controller. Since the memory on the controller is
        limited, the AR488 can buffer only 120 characters at a time.
        When sending data followed by a command, the buffer must first be read by the controller before
        a subsequent command can be accepted, otherwise the command will be treated as characters to
        be appended to the existing data in the buffer."""
        if new_mode is None:
            return self._valid_mode[int(self.query('++mode'))]
        else:
            if type(new_mode) == str and new_mode not in self._valid_mode:
                raise Exception('invalid interface operation mode')
            else:
                new_mode = self._valid_mode.index(new_mode)  # get mode index

            if type(new_mode) == int and new_mode in range(len(self._valid_mode)):
                self.bus_write(f'++mode {self._valid_mode[new_mode]}')
            else:
                raise Exception('invalid mode type')

            # check
            self._mode = self.mode()  # string
            if self._mode != new_mode:
                raise Exception('unable to set correct operation mode')

    def read(self, terminator: str = None, decode:bool=True, until_eoi:bool=False):
        """This command can be used to read data from the currently addressed instrument. Data is read
        until:
         the EOI signal is detected
         a specified character is read
         timeout expires
        Timeout is set using the read_tmo_ms command (still to be implemented) and is the maximum permitted
        delay for a single character to be read. It is not related to the time taken to read all the data.
        For details see the description of the read_tmo_ms command."""
        if until_eoi:
            if not self._eoi:
                raise Exception('EOI function not enabled')
            return self.query(f'++read eoi', decode=decode)
        else:
            return self.query(f'++read{" " + terminator if terminator is not None else ""}',
                              decode=(decode if decode is not None else None))

    # todo : ++read_to_ms

    def prologix_reset(self):
        """Perform a reset of the controller."""
        self.bus_write('++rst')

    # todo : ++savecfg

    def spoll(self, targets=None):
        """Performs a serial poll. If no parameters are specified, the command will perform a serial poll of the
        currently addressed instrument. If a GPIB address is specified, then a serial poll of the instrument
        at the specified address is performed. The command returns a single 8-bit decimal number
        representing the status byte of the instrument.
        The command can also be used to serial poll multiple instruments. Up to 15 addresses can be
        specified. If the all parameter is specified, then a serial poll of all 30 primary instrument addresses
        is performed.
        When polling multiple addresses, the prologix_spoll() command will return the address and status byte of
        the first instrument it encounters that has the RQS bit set in its status byte, indicating that it has
        requested service. The format of the response is SRQ:addr,status, for example: SRQ:3,88 where 3
        is the GPIB address of the instrument and 88 is the status byte. The response provides a means to
        poll a number of instruments and to identify which instrument raised the service request, all in
        one command. If SRQ was not asserted then no response will be returned.
        When ++srqauto is set to 1 (for details see the ++srqauto custom command), the interface will
        automatically conduct a serial poll of all devices on the GPIB bus whenever it detects that SRQ has
        been asserted and the details of the instrument that raised the request are automatically returned
        to the format above."""
        target_string = ''
        if targets is not None:
            if type(targets) == list or type(targets) == tuple:
                if len(targets) < 15:
                    target_string += ' all '
                    for i in targets:
                        target_string += f' {i}'
                else:
                    raise Exception('too many spoll addresses, max is 15')
            elif type(targets) == int and 0 < targets < 30:
                target_string += f' {targets}'

        return self.query('++spoll' + target_string)

    def read_srq(self):
        """This command returns the present status of the SRQ signal line. It returns False if SRQ is not asserted
        and True if SRQ is asserted"""
        return bool(self.query('++srq'))

    # todo : ++status

    def send_trigger(self, target):
        """Sends a Group Execute Trigger to selected devices. Up to 15 addresses may be specified and must
        be separated by spaces. If no address is specified, then the command is sent to the currently
        addressed instrument. The instrument needs to be set to single trigger mode and remotely
        controlled by the GPIB controller. Using ++trg, the instrument can be manually triggered and the
        result read with prologix_read()"""
        if type(target) == int and 1 <= target <= 30:
            self.bus_write(f'++trg {target}')
        elif type(target) == list or type(target) == tuple:
            if len(target) > 15:
                raise Exception(
                    'too many targets, group trigger support max 15 devices ')
            target_string = ''
            for i in target:
                if i == int and 1 <= i == 30:
                    target_string += f' {i}'
                else:
                    raise Exception('invalid type in trigger targets')
            self.bus_write('trg' + target_string)
        else:
            raise Exception('invalid type of trigger target')

    def ver(self):
        """Display the controller firmware version. If the version string has been changed with ++setvstr
        ( still to be implemented ), then prologix_ver() will display the new version string. Issuing the command
        with the parameter ‘real’ will always display the original AR488 version string"""
        return self.bus_write('++ver')

    # custom commands
    # todo : ++allspoll,

    def prologix_device_clear(self):
        """Send Device Clear (DCL) to all devices on the GPIB bus."""
        self.bus_write('++dcl')

    # todo : ++default

    def eor(self, new_eor: str = None):
        """End of receive. While prologix_eos(str) (end of send) selects the terminator to add to commands and data
        being sent to the instrument, the prologix_eor(str) command selects the expected termination sequence
        when receiving data from the instrument. The default termination sequence is CR + LF.
        If the command is specified with one of the above numeric options, then the corresponding termination
        sequence will be used to detect the end of the data being transmitted from the instrument. If the command
        is specified without a parameter, then it will return the current setting. If option "EOI" is selected,
        then prologix_read() eoi is implied for all prologix_read() instructions as well as any data being returned by
        the instrument in response to direct instrument commands. An EOI is expected to be signalled by the instrument
        with the last character of any transmission sent. All characters sent over the GPIB bus are passed to the
        serial port for onward transmission to the host computer"""
        if new_eor is None:
            return self._valid_eor[int(self.query('++eor'))]
        else:
            if new_eor in self._valid_eor:
                self.bus_write(f'++eor {self._valid_eor.index(new_eor)}')
            else:
                raise Exception('invalid eor char sequence')

            # check
            current_eor = self.eor()
            if current_eor != new_eor:
                raise Exception('unable to set new eor char sequence')

    # todo : ++id, ++id fwver, ++id serial, ++id verstr

    def idn(self, new_idn=None):
        """This command is used to enable the facility for the interface to respond to a SCPI *idn? Command.
        Some older instruments do no respond to a SCPI ID request but this feature will allow the interface
        to respond on behalf of the instrument using parameters set with the ++id command. When set to
        zero, response to the SCPI *idn? command is disabled and the request is passed to the instrument.
        When set to 1, the interface responds with the name set using the ++idn name command. When
        set to 2, the instrument also appends the serial number using the format name-99999999"""
        if new_idn is None:
            return self.query('++idn')
        else:
            if 0 <= new_idn <= 2:
                self.bus_write(f'++idn {new_idn}')
            else:
                raise Exception('invalid idn mode')

            self._idn = self.idn()
            if self._idn != new_idn:
                raise Exception('unable to set new idn mode')

    # todo : ++macro, ++ppoll, ++prom, ++ren, ++repeat, ++setvstr, ++srqauto, ton, ++verbose

# notes:
# '\r', '\n', and '+' are control characters that must be escaped in binary data
#
# Prologix commands:
# ++addr [1-29]
# ++auto [0 | 1 | 2 | 3]
# ++clr
# ++eoi [0 | 1]
# ++eos [0 | 2 | 3 | 4]
# ++eot_enable [0 | 1]
# ++eot_char [<char>]
# ++help (unsupported)
# ++ifc
# ++llo [all]
# ++loc [all]
# ++lon (unsupported)
# ++mode [0 | 1]
# ++read [eoi | <char>]
# ++read_tmo_ms <time>
# ++rst
# ++savecfg
# ++spoll [<PAD> | all | <PAD1> <PAD2> <PAD3> ...]
# ++srq
# ++status [<byte>]
# ++trg [PAD1 ... PAD15]
# ++ver [real]
#
# Custom AR488 commands:
# ++allspoll
# ++dl
# ++default
# ++macro [1-9]
# ++ppoll
# ++setvstr [string]
# ++srqauto [0 | 1]
# ++repeat count delay cmdstring
# ++tmbus [value]
# ++verbose