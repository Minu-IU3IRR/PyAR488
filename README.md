
package to interact with AR488 interface boards, adds a bit of abstraction to simplify interactions. also can be passed as an argument to custom classes to semplify instrument contorl in your code like :

    from PyAR488.PyAR488 import AR488
    
    class HP3468A:
        def __init__(gpib_addrs:int, interface:AR488):
            self.address = gpib_addrs
            self.interface = interface

        def read_measurement(self):
            self.interface.address(self.address)
            return self.interface.read()


    my_awesome_interface = AR488('COM5')  # open the interface
    my_swesome_meter = HP3468A(22 , my_awesome_interface)  # create the interument object

    reading = my_awesome_meter.read_measurement()  #read measurement
    print(reading)


NOTE : for custom instrument classes remember that the interface must be on the same address as the instrument to comunicate, maybe implement a custom function like:

    class MyAwesomeInstrument:
        def __init__(self, interface:AR488, address:int):  #define instruemtn with interface and GPIB address
            self.interface = interface
            self.address = address
    
        def _read(messsage:str):  # internal function that make sure the address has not been changed before the operation
            self.interface.address(self.address):
            return self.interface.read(message)
    
This way you are shoure that the interface is always on the right address and the serial command to change is sent only if it is currently configured diferently (so no useless traffic on usb). all is handeled automaticaly in the PyAR488 module.

In case of trouble... enable the debung on object declaration to see printed each and every command sent to the interface and your instruments! 

just use:

    from PyAR488.PyAR488 import AR488
    my_interface = AR488('COM5', debug = True)

if you face any problen make sure to send an issue on GitHub or make a pull request with the fix!
GitHub repo: https://github.com/Minu-IU3IRR/PyAR488
