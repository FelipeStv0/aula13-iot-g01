"""ESP32 + DS18B20. HTTPS direto. Sem segredo no arquivo publico."""
from machine import Pin
import network, onewire, ds18x20, time, json, random, socket, ssl
from ubinascii import a2b_base64

HOST = "ckccllcmaepeamftkkew.supabase.co"
# Certificados-raiz PUBLICOS, em DER/base64 (Mozilla trust store).
# GTS Root R4, GTS Root R1, ISRG Root X2.
ROOTS = (
    "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",
)
sensor = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
roms = sensor.scan()
if not roms:
    raise RuntimeError("DS18B20 ausente: confira GPIO4 e diagram.json")
yellow = Pin(19, Pin.OUT, value=0)
red = Pin(18, Pin.OUT, value=0)
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

def alert(avg, prev):
    if avg >= 90:
        return "critical"
    if prev == "critical":
        return "critical" if avg >= 85 else ("warning" if avg >= 65 else "normal")
    if prev == "warning":
        return "warning" if avg >= 65 else "normal"
    return "warning" if avg >= 70 else "normal"

def connect():
    if not wifi.isconnected():
        # Reset the station before retrying, including a failed association.
        wifi.active(False)
        time.sleep_ms(500)
        wifi.active(True)
        time.sleep_ms(500)
        print("Wi-Fi: conectando a Wokwi-GUEST...")
        wifi.connect("Wokwi-GUEST", "")
        begin = time.ticks_ms()
        last_log = begin
        while not wifi.isconnected():
            now = time.ticks_ms()
            if time.ticks_diff(now, last_log) >= 5000:
                print("Wi-Fi status:", wifi.status())
                last_log = now
            if time.ticks_diff(now, begin) >= 45000:
                raise OSError("Wi-Fi timeout; status=" + str(wifi.status()))
            time.sleep_ms(200)
        print("Wi-Fi conectado | IP:", wifi.ifconfig()[0])
    if time.localtime()[0] < 2024:
        import ntptime
        ntptime.settime()
    if time.localtime()[0] < 2024:
        raise OSError("RTC invalido; TLS requer horario correto")

trusted_index = 0

def secure_connection():
    global trusted_index
    address = socket.getaddrinfo(HOST, 443, 0, socket.SOCK_STREAM)[0][-1]
    last_error = None
    # Cada tentativa valida o certificado e o hostname; nunca CERT_NONE.
    for i in [trusted_index] + [n for n in range(len(ROOTS)) if n != trusted_index]:
        sock = socket.socket()
        try:
            sock.settimeout(8)
            sock.connect(address)
            conn = ssl.wrap_socket(sock, server_hostname=HOST,
                cert_reqs=ssl.CERT_REQUIRED, cadata=a2b_base64(ROOTS[i]))
            trusted_index = i
            return conn
        except Exception as exc:
            last_error = exc
            sock.close()
    raise OSError("TLS: " + str(last_error))

def post(payload, key):
    connect()
    body = json.dumps(payload).encode()
    conn = secure_connection()
    try:
        req = ("POST /functions/v1/ingest HTTP/1.1\r\nHost: " + HOST +
               "\r\nContent-Type: application/json\r\nx-ingest-key: " + key +
               "\r\nConnection: close\r\nContent-Length: " + str(len(body)) +
               "\r\n\r\n").encode() + body
        sent = 0
        while sent < len(req):
            count = conn.write(req[sent:])
            if not count:
                raise OSError("Escrita TLS incompleta")
            sent += count
        status = conn.readline().split()
        if len(status) < 2:
            raise OSError("Resposta HTTP invalida")
        return int(status[1])
    finally:
        conn.close()

print("VRM G01 | sensor DS18B20 encontrado")
print("Digite INGEST_KEY no terminal e Enter; Enter vazio = modo local.")
print("A chave fica em RAM, nao no codigo. Nao grave o momento da digitacao.")
key = input("Chave: ").strip()
if any(c in key for c in "\r\n"):
    raise ValueError("Chave invalida")
samples = []
state = "normal"
boot = "%08x" % random.getrandbits(32)
seq = 0
pending = None
last_sample = time.ticks_add(time.ticks_ms(), -2000)
last_upload = time.ticks_add(time.ticks_ms(), -10000)
while True:
    now = time.ticks_ms()
    if time.ticks_diff(now, last_sample) >= 2000:
        last_sample = now
        try:
            sensor.convert_temp()
            time.sleep_ms(750)
            raw = sensor.read_temp(roms[0])
            if raw is not None and -55 <= raw <= 125:
                samples.append(round(raw, 2))
                if len(samples) > 3:
                    samples.pop(0)
                avg = round(sum(samples) / len(samples), 2)
                state = alert(avg, state)
                yellow.value(state == "warning")
                red.value(state == "critical")
                print("DS18B20", raw, "C | media", avg, "| alerta", state)
            else:
                print("Leitura invalida")
        except Exception as exc:
            print("Erro sensor:", exc)
    if samples and key and time.ticks_diff(time.ticks_ms(), last_upload) >= 10000:
        last_upload = time.ticks_ms()
        if pending is None:
            seq += 1
            pending = dict(device_id="esp32_g01", message_id=boot+"-"+str(seq),
                measurement="temperature", value=round(sum(samples)/len(samples),2),
                raw_value=samples[-1], unit="C", alert=state, sample_count=len(samples))
        try:
            status = post(pending, key)
            print("POST", pending["message_id"], "HTTP", status)
            if status in (200, 201):
                pending = None
            elif status in (401, 403):
                print("Autenticacao recusada. Reinicie e confira INGEST_KEY.")
                key = ""
                pending = None
            elif status == 400:
                print("Payload recusado")
                pending = None
        except Exception as exc:
            print("Falha HTTPS; tentara novamente:", exc)
    time.sleep_ms(100)
