"""Monitoramento VRM simulado; config.py e CA local para HTTPS."""
from machine import Pin
import network, onewire, ds18x20, time, json, random, socket, ssl
try:
    import config
except ImportError:
    class config:
        WIFI_SSID = "Wokwi-GUEST"
        WIFI_PASSWORD = ""
        INGEST_KEY = ""
HOST = "ckccllcmaepeamftkkew.supabase.co"
sensor = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
roms = sensor.scan()
if not roms:
    raise RuntimeError("DS18B20 ausente")
yellow = Pin(19, Pin.OUT)
red = Pin(18, Pin.OUT)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
samples = []
state = "normal"
boot = "%08x" % random.getrandbits(32)
seq = 0
pending = None
last_sample = time.ticks_add(time.ticks_ms(), -2000)
last_send = time.ticks_add(time.ticks_ms(), -10000)

def update_alert(avg, prev):
    if avg >= 90:
        return "critical"
    if prev == "critical":
        return "critical" if avg >= 85 else ("warning" if avg >= 65 else "normal")
    if prev == "warning":
        return "warning" if avg >= 65 else "normal"
    return "warning" if avg >= 70 else "normal"

def send(payload):
    if not wifi.isconnected():
        wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        start = time.ticks_ms()
        while not wifi.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 15000:
                raise OSError("Wi-Fi timeout")
            time.sleep_ms(200)
    if time.localtime()[0] < 2024:
        import ntptime
        ntptime.settime()
    if time.localtime()[0] < 2024:
        raise OSError("RTC invalido")
    with open("supabase-ca.pem","rb") as f:
        ca = f.read()
    body = json.dumps(payload).encode()
    addr = socket.getaddrinfo(HOST,443,0,socket.SOCK_STREAM)[0][-1]
    sock = socket.socket()
    sock.settimeout(8)
    tls = None
    try:
        sock.connect(addr)
        tls = ssl.wrap_socket(sock,server_hostname=HOST,cert_reqs=ssl.CERT_REQUIRED,cadata=ca)
        req = ("POST /functions/v1/ingest HTTP/1.1\r\nHost: "+HOST+
            "\r\nContent-Type: application/json\r\nx-ingest-key: "+config.INGEST_KEY+
            "\r\nConnection: close\r\nContent-Length: "+str(len(body))+"\r\n\r\n").encode()+body
        sent = 0
        while sent < len(req):
            n = tls.write(req[sent:])
            if not n:
                raise OSError("Falha de escrita TLS")
            sent += n
        return int(tls.readline().split()[1])
    finally:
        (tls if tls else sock).close()

while True:
    now = time.ticks_ms()
    if time.ticks_diff(now,last_sample) >= 2000:
        last_sample = now
        try:
            sensor.convert_temp()
            time.sleep_ms(750)
            t = sensor.read_temp(roms[0])
            if t is not None and -55 <= t <= 125:
                samples.append(round(t,2))
                if len(samples)>3:
                    samples.pop(0)
                avg = round(sum(samples)/len(samples),2)
                state = update_alert(avg,state)
                yellow.value(state=="warning")
                red.value(state=="critical")
                print("DS18B20",t,"C | media",avg,"| alerta",state)
        except Exception as e:
            print("Erro de aquisicao:",e)
    if samples and time.ticks_diff(now,last_send)>=10000:
        last_send = now
        if config.INGEST_KEY and not config.INGEST_KEY.startswith("COLE_"):
            if pending is None:
                seq += 1
                pending = dict(device_id="esp32_g01",message_id=boot+"-"+str(seq),
                    measurement="temperature",value=round(sum(samples)/len(samples),2),
                    raw_value=samples[-1],unit="C",alert=state,sample_count=len(samples))
            try:
                status = send(pending)
                print("HTTPS POST",pending["message_id"],"HTTP",status)
                if status in (200,201,400,401,403):
                    pending = None
            except Exception as e:
                print("Falha HTTPS; mensagem pendente",type(e).__name__)
        else:
            print("Modo local: sem chave de ingestao")
    time.sleep_ms(100)
