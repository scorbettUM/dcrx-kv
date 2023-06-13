from dcrx_kv.context.types import ContextType
from dcrx_kv.env import Env
from pydantic import (
    BaseModel,
    StrictStr
)
from .cpu import CPUMonitor
from .memory import (
    MemoryMonitor
)



class MonitoringServiceContext(BaseModel):
    env: Env
    monitor_name: StrictStr
    cpu: CPUMonitor
    memory: MemoryMonitor
    context_type: ContextType=ContextType.MONITORING_SERVICE

    class Config:
        arbitrary_types_allowed = True

    @property
    def exceeded_memory_limit(self) -> bool:
        return self.get_memory_usage_pct() > self.env.DCRX_KV_MAX_MEMORY_PERCENT_USAGE

    def get_memory_usage_pct(self) -> float:
        return self.memory.get_percent_used(self.monitor_name)

    async def initialize(self):
        await self.cpu.start_background_monitor(self.monitor_name)
        await self.memory.start_background_monitor(self.monitor_name)

    async def close(self):
        await self.cpu.stop_background_monitor(self.monitor_name)
        await self.memory.stop_background_monitor(self.monitor_name)