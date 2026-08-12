import socket, sys


def probe(host, port, timeout=5.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, int(port))); return "OPEN"
    except socket.timeout: return "TIMEOUT"
    except ConnectionRefusedError: return "REFUSED"
    except OSError as e:
        return "OSERROR:" + (e.strerror or type(e).__name__).replace(" ", "_")
    finally: s.close()


if __name__ == "__main__":
    for spec in sys.argv[1:]:
        h, _, p = spec.rpartition(":")
        print(spec + " " + probe(h, p))
