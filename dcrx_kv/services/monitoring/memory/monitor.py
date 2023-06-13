import os
import psutil
from dcrx_kv.services.monitoring.base.monitor import BaseMonitor


class MemoryMonitor(BaseMonitor):

    def __init__(self) -> None:
        super().__init__()
        self.total_memory = int(psutil.virtual_memory().total/10**6)
    
    def get_percent_used(self, monitor_name) -> float:
        precentile_usage_metric = f'{monitor_name}_pct_usage'
        return self.active.get(precentile_usage_metric, 0)

    def update_monitor(self, monitor_name: str):

        self.active[monitor_name] = int(psutil.virtual_memory().used/10**6)

        precentile_usage_metric = f'{monitor_name}_pct_usage'
        self.active[precentile_usage_metric] = psutil.virtual_memory().percent