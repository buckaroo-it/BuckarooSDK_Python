import ipaddress

IPV4 = 0
IPV6 = 1


def get_version(ip_address: str) -> int:
    try:
        ip = ipaddress.ip_address(ip_address)
        return IPV6 if ip.version == 6 else IPV4
    except ValueError:
        return IPV4
