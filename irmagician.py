import sys, serial, time, json


class IrMagician:

    def __init__(self, dev = '/dev/ttyACM0', timeout = 1):
        self.debug = False
        self.logs = []
        self.open(dev, timeout)
        
    def set_debug(self, b):
        self.debug = b

    def log(self, s):
        if not self.debug: return
        self.logs.append(s)
        print('irMag:', s.strip())

    def open(self, dev = '/dev/ttyACM0', timeout = 1):
        self.ser = serial.Serial(dev, 9600, timeout = 1)

    def close(self):
        self.ser.close()

    def write(self, s):
        b = s.encode('utf-8') # bytesに変換
        self.ser.write(b)
        self.log("write=" + s)
        
    def readline(self):
        b = self.ser.readline()
        s = b.decode('utf-8')
        self.log("read=" + s)
        return s
        
    def command(self, cmd, wait=1):
        self.write(cmd)
        time.sleep(wait)
        return self.readline()
        
    def read(self, num = 1):
        b = self.ser.read(num)
        return b

    # バッファをクリアする関数
    def clear_buf(self):
        self.command("R,0\r\n", 1.0)

    def ir_capture(self):
        r = self.command("c\r\n", 0.3)
        time.sleep(3.0)
        return self.readline()

    def ir_capture_ex(self):
        self.clear_buf()
        print("> 赤外線リモコンのボタンを押してください")
        while True:
            r = self.ir_capture()
            if r.find("Time Out") > 0 or r == "":
                print("失敗(ToT)")
                continue
            print("ok")
            break

    def ir_save(self, savefile):
        # まずは信号のサイズを得る
        ir_size_s = self.command("I,1\r\n", 1.0)
        ir_size = int(ir_size_s, 16)
        self.log("ir_size=" + str(ir_size))

        # postscalerを得る
        postscale_str = self.command("I,6\r\n")
        postscale = int(postscale_str)
        self.log("postscale=" +  postscale_str)

        # 順に信号を読む
        values = []
        for n in range(ir_size):
            bank = n // 64
            pos = n % 64
            if (pos == 0): # バンク切替
                self.write("b,%d\r\n" % bank)
            # 信号を読む
            self.write("d,%d\r\n" % pos)
            xs = self.read(3)
            v = int(xs, 16)
            values.append(v)

        # JSONでファイルに保存
        json_data = {
            'format':'raw', 'freq':38, 'data':values,
            'postscale':postscale}
        f = open(savefile, "w")
        json.dump(json_data, f)
        f.close()
        self.log("saved")

    def ir_load(self, infile):
        """ ファイルから読み出してirMagicianに転送する"""
        # ファイルからJSONデータを読む
        f = open(infile, 'r')
        json_data = json.load(f)
        f.close()
        ir_size = len(json_data['data'])
        values = json_data['data']

        # 送信バイト数を送信
        self.command("n,%d\r\n" % ir_size, 0.1)
        # postScaleを送信
        postscale = json_data['postscale']
        self.command("k,%d\r\n" % postscale, 0.1)
        # 各バイトを送信
        for n in range(ir_size):
            bank = n // 64
            pos = n % 64
            if (pos == 0):
                self.write("b,%d\r\n" % bank)
            self.write("w,%d,%d\n\r" % (pos, values[n]))

    def ir_play(self):
        self.command("p\r\n")

    def get_temperature(self):
        raw = self.command("T\r\n") # reading rw temp...
        status = self.readline() # reading command status
        celsius_temp = None
        try:
            celsius_temp = ((5.0 / 1024.0 * float(raw)) - 0.4) / 0.01953
            return celsius_temp
        except (ValueError, TypeError):
            return None

if __name__ == '__main__':
    mag = IrMagician()
    mag.set_debug(True)
    mag.ir_capture_ex()
    mag.ir_save("test.json")
    mag.ir_load("test.json")
    mag.ir_play()
    print("temp="+mag.get_temperature())


