"""VRM G01: DS18B20 e HTTPS direto. Nao ha credenciais no arquivo."""
from machine import Pin
import network, onewire, ds18x20, time, json, random, socket, ssl
from ubinascii import a2b_base64

HOST = "ckccllcmaepeamftkkew.supabase.co"
SSID = "Wokwi-GUEST"
BSSID = b"\x42\x13\x37\x55\xaa\x01"
# CAs publicas em DER/base64, extraidas do trust store Mozilla.
ROOTS = (
    'MIICCTCCAY6gAwIBAgINAgPlwGjvYxqccpBQUjAKBggqhkjOPQQDAzBHMQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEUMBIGA1UEAxMLR1RTIFJvb3QgUjQwHhcNMTYwNjIyMDAwMDAwWhcNMzYwNjIyMDAwMDAwWjBHMQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEUMBIGA1UEAxMLR1RTIFJvb3QgUjQwdjAQBgcqhkjOPQIBBgUrgQQAIgNiAATzdHOnaItgrkO4NcWBMHtLSZ37wWHO5t5GvWvVYRg1rkDdc/eJkTBa6zzuhXyiQHY7qca4R9gq55KRanPpsXI5nymfopjTX15YhmUPoYRlBtHci8nHc8iMai/lxKvRHYqjQjBAMA4GA1UdDwEB/wQEAwIBhjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBSATNbrdP9JNqPV2Py1PsVq8JQdjDAKBggqhkjOPQQDAwNpADBmAjEA6ED/g94D9J+uHXqnLrmvT/aDHQ4thQEd0dlq7A/Cr8deVl5c1RxYIigL9zC2L7F8AjEA8GE8p/SgguMh1YQdc4acLa/KNJvxn7kjNuK8YAOdgLOaVsjh4rsUecrNIdSUtUlD',  # GTS_Root_R4
    'MIIFVzCCAz+gAwIBAgINAgPlk28xsBNJiGuiFzANBgkqhkiG9w0BAQwFADBHMQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEUMBIGA1UEAxMLR1RTIFJvb3QgUjEwHhcNMTYwNjIyMDAwMDAwWhcNMzYwNjIyMDAwMDAwWjBHMQswCQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEUMBIGA1UEAxMLR1RTIFJvb3QgUjEwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQC2EQKLHuOhd5s73L+UPreVp0A8of2C+X0yBoJx9vaMf/vo27xqLpeXo4xL+Sv2sfnOhB2x+cWX3u+58qPpvBKJXqeqUqv4IyfLpLGcY9vXmX7wCl7raKb0xlpHDU0QM+NOsROjyBhsS+z8CZDfnWQpJSMHobTSPS5g4M/SCYe7zUjwTcLCeoiKu7rPWRnWr4+wB7CeMfGCwcDfLqZtbBkOtdh+JhpFAz2weaSUKK0PfyblqAj+lug8aJRT7oM6iCsVlgmy4HqMLnXWnOunVmSPlk9orj2XwoSPwLxAwAtcvfaHszVsrBhQf4TgTM2S0yDpM7xSma8ytSmzJSq0SPly4cpk9+aCEI3oncKKiPo4Zor8Y/kB+Xj9e1x3+naH+uzfsQ55lVe0vSbv1gHR6xYKu44LtcXFilWr06zqkUspzBmkMiVOKvFlRNACzqrOSbTqn3yDsEB750Orp2yjj32JgfpMpf/VjsPOS+C12LOORc92wO1AK/1TD7Cn1TsNsYqiA94xrcx36m97PtbfkSIS5r762DL8EGMUUXLeXdYWk70paDPvOmbsB4om3xPXV2V4J95eSRQAogB/mqghtqmxlbCluQ0WEdrHbEg8QOB+DVrNVjzRlwW5y0vtOUucxD/SVRNuJLDWcfr0wbrM7Rv1/oFB2ACYPTrIrnqYNxgFlQIDAQABo0IwQDAOBgNVHQ8BAf8EBAMCAYYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU5K8rJnEaK0gnhS9SZizv8IkTcT4wDQYJKoZIhvcNAQEMBQADggIBAJ+qQibbC5u+/x6Wki4+omVKapi6Ist9wTrYggoGxval3sBOh2Z5ofmmWJyq+bXmYOfg6LEeQkEzCzc9zolwFcq1JKjPa7XSQCGYzyI0zzvFIoTgxQ6KfF2I5DUkzps+GlQebtuyh6f88/qBVRRiClmpIgUxPoLW7ttXNLwzldMXG+gnoot7TiYaelpkttGsN/H9oPM47HLwEXWdyzRSjeZ2axfG34arJ45JK3VmgRAhpuo+9K4l/3wV3s6MJT/KYnAK9y8JZgfIPxz88NtFMN9iiMG1D53Dn0reWVlHxYciNuaCp+0KueIHoI17eko8cdLiA6EfMgfdG+RCzgwARWGAtQsgWSl4vflVy2PFPEz0tv/bal8xa5meLMFrUKTX5hgUvYU/Z6tGn6D/Qqc6f1zLXbBwHSs09dR2CQzreExZBfMzQsNhFRAbd03OIozUhfJFfbdT6u9AWpQKXCBfTkBdYiJ23//OYb2MI3jSNwLgjt7RETeJ9r/tSQdirpLsQBqvFAnZ0E6yove+7u7Y/9waLd64NnHi/Hm3lCXRSHNboTXns5lndcEZOitHTtNCjv0xyBZm2tIMPNuzjsmhDYAPexZ3FL//2wmUspO8IFgV6dtxQ/PeEMMA3KgqlbbC1j+Qa3bbbP6MvPJwNQzcmRk13NfIRmPVNnGuV/u3gm3c',  # GTS_Root_R1
    'MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAwTzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2VhcmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJuZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBYMTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygch77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6UA5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sWT8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyHB5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UCB5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUvKBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWnOlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTnjh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbwqHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CIrU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkqhkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZLubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KKNFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7UrTkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdCjNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVcoyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPAmRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57demyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=',  # ISRG_Root_X1
    'MIICGzCCAaGgAwIBAgIQQdKd0XLq7qeAwSxs6S+HUjAKBggqhkjOPQQDAzBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJuZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBYMjAeFw0yMDA5MDQwMDAwMDBaFw00MDA5MTcxNjAwMDBaME8xCzAJBgNVBAYTAlVTMSkwJwYDVQQKEyBJbnRlcm5ldCBTZWN1cml0eSBSZXNlYXJjaCBHcm91cDEVMBMGA1UEAxMMSVNSRyBSb290IFgyMHYwEAYHKoZIzj0CAQYFK4EEACIDYgAEzZvVn4CDCuwJSvMWSj5cz3es3mcFDR0HttwW+1qLFNvicWDEukWVEYmO6gbf9yoWHKS5xcUy4APgHoIYOIvXRdgKam7mAHf7AlF9ItgKbppbd9/w+kHsOdx1ymgHDB/qo0IwQDAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUfEKWrt5LSDv6kviejM9ti6lyN5UwCgYIKoZIzj0EAwMDaAAwZQIwe3lORlCEwkSHRhtFcP9Ymd70/aTSVaYgLXTWNLxBo1BfASdWtL4ndQavEi51mI38AjEAi/V3bNTIZargCyzuFJ0nN6T5U6VR5CmD1/iQMVtCnwr1/q4AaOeMSQ+2b1tbFfLn',  # ISRG_Root_X2
)


def alert(avg, prev):
    if avg >= 90:
        return "critical"
    if prev == "critical":
        return "critical" if avg >= 85 else ("warning" if avg >= 65 else "normal")
    if prev == "warning":
        return "warning" if avg >= 65 else "normal"
    return "warning" if avg >= 70 else "normal"


class WifiLink:
    """Conexao oficial por SSID; fallback BSSID sem scan bloqueante."""
    def __init__(self, sta):
        self.sta = sta
        self.phase = "idle"
        self.attempt = 0
        self.deadline = 0
        self.last_log = 0

    def tick(self, now):
        w = self.sta
        if w.isconnected():
            if self.phase != "online":
                print("Wi-Fi conectado | IP:", w.ifconfig()[0])
            self.phase = "online"
            self.attempt = 0
            return True
        if self.phase == "online":
            # Deixar o driver tentar reconectar sem destruir a interface.
            print("Wi-Fi caiu; aguardando reconexao automatica")
            self.phase = "waiting"
            self.deadline = time.ticks_add(now, 60000)
            self.last_log = now
        if self.phase == "waiting":
            if time.ticks_diff(now, self.last_log) >= 5000:
                print("Wi-Fi status:", w.status())
                self.last_log = now
            if time.ticks_diff(now, self.deadline) < 0:
                return False
            print("Wi-Fi: sem IP apos 60 s; reiniciando interface")
            try:
                w.disconnect()
            except OSError:
                pass
            w.active(False)
            self.phase = "cooldown"
            self.deadline = time.ticks_add(now, 3000)
            return False
        if self.phase == "cooldown" and time.ticks_diff(now, self.deadline) < 0:
            return False
        if self.phase in ("idle", "cooldown"):
            w.active(True)
            try:
                w.config(reconnects=-1)
            except (OSError, ValueError, TypeError):
                pass
            self.phase = "ready"
            self.deadline = time.ticks_add(now, 1000)
            return False
        if self.phase == "ready" and time.ticks_diff(now, self.deadline) < 0:
            return False
        self.attempt += 1
        try:
            print("Wi-Fi: tentativa", self.attempt, "em", SSID)
            if self.attempt % 2:
                w.connect(SSID, "")
            else:
                try:
                    w.connect(SSID, "", bssid=BSSID)
                except (TypeError, ValueError, OSError):
                    w.connect(SSID, "")
            self.phase = "waiting"
            self.last_log = now
            self.deadline = time.ticks_add(now, 60000)
        except OSError as exc:
            print("Wi-Fi erro:", exc)
            w.active(False)
            self.phase = "cooldown"
            self.deadline = time.ticks_add(now, 3000)
        return False


# MicroPython v1.28 / mbedTLS: cada chamada acrescenta a CA ao contexto.
# Nao alternar a CA em caso de EOF ou outro erro de transporte.
tls_context = None


def get_tls_context():
    global tls_context
    if tls_context is None:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.verify_mode = ssl.CERT_REQUIRED
        for root in ROOTS:
            context.load_verify_locations(cadata=a2b_base64(root))
        tls_context = context
        print("TLS: 4 CAs carregadas; verificacao de hostname ativa")
    return tls_context


def post(payload):
    if time.localtime()[0] < 2024:
        import ntptime
        ntptime.settime()
    if time.localtime()[0] < 2024:
        raise OSError("Relogio invalido para TLS")
    context = get_tls_context()
    address = socket.getaddrinfo(HOST, 443, 0, socket.SOCK_STREAM)[0][-1]
    sock = socket.socket()
    tls = None
    try:
        sock.settimeout(8)
        sock.connect(address)
        tls = context.wrap_socket(sock, server_hostname=HOST,
                                  do_handshake_on_connect=True)
        body = json.dumps(payload).encode()
        req = ("POST /functions/v1/ingest-demo HTTP/1.1\r\nHost: " + HOST +
               "\r\nContent-Type: application/json" +
               "\r\nConnection: close\r\nContent-Length: " + str(len(body)) +
               "\r\n\r\n").encode() + body
        sent = 0
        while sent < len(req):
            n = tls.write(req[sent:])
            if not n:
                raise OSError("Escrita TLS incompleta")
            sent += n
        line = tls.readline()
        fields = line.split()
        if len(fields) < 2 or not fields[0].startswith(b"HTTP/"):
            raise OSError("Resposta HTTP invalida")
        return int(fields[1])
    finally:
        # Erro de fechamento nao deve ocultar o HTTP 201 nem a causa original.
        try:
            if tls is not None:
                tls.close()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass


def make_payload(samples, state, boot, seq):
    return dict(device_id="esp32_g01", message_id="wokwi-demo-"+boot+"-"+str(seq),
                measurement="temperature", value=round(sum(samples)/len(samples),2),
                raw_value=samples[-1], unit="C", alert=state, sample_count=len(samples))


def main():
    ds = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
    roms = ds.scan()
    if not roms:
        raise RuntimeError("DS18B20 ausente no GPIO4")
    yellow = Pin(19, Pin.OUT, value=0)
    red = Pin(18, Pin.OUT, value=0)
    print("VRM G01 v7 | demonstracao publica limitada | DS18B20 encontrado")
    print("Envio automatico: nenhuma chave precisa ser digitada.")
    sta = network.WLAN(network.STA_IF)
    link = WifiLink(sta)
    samples, state = [], "normal"
    boot = "%08x" % (random.getrandbits(32) or 1)
    seq, pending = 0, None
    last_sample = time.ticks_add(time.ticks_ms(), -2000)
    last_send = time.ticks_add(time.ticks_ms(), -10000)
    conversion = None
    demo_active = True
    while True:
        now = time.ticks_ms()
        if conversion is None and time.ticks_diff(now,last_sample)>=2000:
            last_sample = now
            try:
                ds.convert_temp()
                conversion = time.ticks_add(now,750)
            except Exception as exc:
                print("Sensor:",exc)
        if conversion is not None and time.ticks_diff(now,conversion)>=0:
            conversion = None
            try:
                raw = ds.read_temp(roms[0])
                if raw is not None and -55 <= raw <= 125:
                    samples.append(round(raw,2))
                    if len(samples)>3:
                        samples.pop(0)
                    avg = round(sum(samples)/len(samples),2)
                    state = alert(avg,state)
                    yellow.value(state=="warning")
                    red.value(state=="critical")
                    print("DS18B20",raw,"C | media",avg,"| alerta",state)
                else:
                    print("Leitura invalida")
            except Exception as exc:
                print("Sensor:",exc)
        online = link.tick(time.ticks_ms()) if demo_active else False
        if online and samples and time.ticks_diff(time.ticks_ms(),last_send)>=10000:
            if pending is None:
                seq += 1
                pending = make_payload(samples,state,boot,seq)
            try:
                status = post(pending)
                print("POST",pending["message_id"],"HTTP",status)
                if status in (200,201,400,413):
                    pending = None
                elif status == 429:
                    print("Limite do modo demo; nova tentativa em 10 s.")
                elif status == 410:
                    print("Demonstracao expirada; sensor continua em modo local.")
                    demo_active = False
                    pending = None
                    last_send = time.ticks_ms()
            except Exception as exc:
                print("HTTPS falhou; nova tentativa em 10 s:",exc)
            finally:
                # Intervalo a partir do fim da tentativa, sem rajadas de POST.
                last_send = time.ticks_ms()
        time.sleep_ms(100)

main()
