import psutil
from dcrx_kv.services.monitoring.base.monitor import BaseMonitor


class CPUMonitor(BaseMonitor):

    def __init__(self) -> None:
        super().__init__()

    def update_monitor(self, monitor_name: str):
        self.active[monitor_name] = psutil.cpu_percent()


        