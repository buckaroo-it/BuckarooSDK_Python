from typing import Optional, Self
import os
import socket

import src.resources.constants.ip_protocol_version as ip_protocol_version
import src.models.model_mixin as model_mixin


class ClientIP(model_mixin.ModelMixin):
    def __init__(self, ip: Optional[str] = None, ip_type: Optional[int] = None):
        self._Type: Optional[int] = None
        self._Address: Optional[str] = None
        self.set_address(ip)
        self.set_type(ip_type)

        self.set_properties()

    def set_address(self, ip: Optional[str]) -> Self:
        self._Address = ip or self.get_remote_ip()
        return self

    def set_type(self, ip_type: Optional[int]) -> Self:
        self._Type = ip_type or ip_protocol_version.get_version(self._Address or "")
        return self

    def get_remote_ip(self):
        x_forwarded_for = os.environ.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
            if self.is_valid_ip(ip):
                return ip

        http_x_forwarded_for = os.environ.get("HTTP_X_FORWARDED_FOR")
        if http_x_forwarded_for:
            ip = http_x_forwarded_for.split(",")[0].strip()
            if self.is_valid_ip(ip):
                return ip

        remote_addr = os.environ.get("REMOTE_ADDR")
        if remote_addr and self.is_valid_ip(remote_addr):
            return remote_addr

        return "127.0.0.1"

    def is_valid_ip(ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
