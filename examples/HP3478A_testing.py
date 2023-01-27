from PyAR488.PyAR488 import AR488
from PyAR488.HP3478A import HP3478A
import time

interface = AR488('COM4')
meter = HP3478A(23,interface)

meter.print_text('PYAR488')
time.sleep(3)
meter.normal_display()

while True:
    print(meter.read())
    time.sleep(1)
