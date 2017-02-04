# python3_irmagician

irMagician Library for Python3

## How to use

```
from irmagician import IrMagician

mag = IrMagician()

# capture and save
mag.ir_capture_ex()
mag.ir_save("test.json")

# load and play
mag.ir_load("test.json")
mag.ir_play()

# get temperature
print("temp="+mag.get_temperature())
```


