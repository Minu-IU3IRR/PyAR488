from time import sleep
from PyAR488.PyAR488 import AR488
from PyAR488.HP436A import HP436A
interface = AR488('COM5')

meter = HP436A(interface, 13)

while True:
    try:
        print(meter.read(all_data=True))
    except meter.OverRange:
        print('WARNING : power too high!')
    except meter.UnderRange:
        print('under range')
    except meter.AutoZeroInProgress:
        print('meter is performing autozero, please wait')
    except meter.AutoZeroOverRange:
        print('WARNING : error performing probe autozero')
    sleep(0.5)