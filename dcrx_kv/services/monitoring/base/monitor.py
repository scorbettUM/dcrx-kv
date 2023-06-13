import asyncio
import functools
import psutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import (
    Dict, 
    List, 
    Union,
    Any
)


WorkerMetrics = Dict[int, Dict[str, List[Union[int, float]]]] 


def handle_thread_loop_stop(
    loop: asyncio.AbstractEventLoop,
    monitor_name: str,
    running_monitors: Dict[str, bool]=None,

):
    running_monitors[monitor_name] = False
    loop.stop()
    loop.close()


class BaseMonitor:

    def __init__(self) -> None:
        self.active: Dict[str, List[int]] = {}
        self.collected: Dict[str, List[int]] = {}
        self.cpu_count = psutil.cpu_count()
        self.stage_metrics: Dict[str, List[Union[int, float]]] = {}
        self.visibility_filters: Dict[str, bool] = defaultdict(lambda: False)
        self.stage_type: Union[Any, None] = None
        self.is_execute_stage = False

        self._background_monitors: Dict[str, asyncio.Task] = {}
        self._sync_background_monitors: Dict[str, asyncio.Future] = {}
        self._running_monitors: Dict[str, bool] = {}

        self._loop: Union[asyncio.AbstractEventLoop, None] = None
        self._executor: Union[ThreadPoolExecutor, None] = None

    def aggregate_worker_stats(self):
        raise NotImplementedError('Aggregate worker stats method method must be implemented in a non-base Monitor class.')

    async def start_background_monitor(
        self,
        monitor_name: str,
        interval_sec: Union[int, float]=1
    ):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=psutil.cpu_count(logical=False)
            )

        self._background_monitors[monitor_name] = self._loop.run_in_executor(
            self._executor,
            functools.partial(
                self._monitor_at_interval,
                monitor_name,
                interval_sec=interval_sec
            )
        )

    def update_monitor(str, monitor_name: str) -> Union[int, float]:
        raise NotImplementedError('Monitor background update method must be implemented in non-base Monitor class.')

    def store_monitor(self, monitor_name: str):
        self.collected[monitor_name] = self.active[monitor_name]
        del self.active[monitor_name]
        
    async def _update_background_monitor(
        self,
        monitor_name: str,
        interval_sec: Union[int, float]=1
    ):
        while self._running_monitors.get(monitor_name):
            await asyncio.sleep(interval_sec)
            self.update_monitor(monitor_name)

    def _monitor_at_interval(
        self, 
        monitor_name: str,
        interval_sec: Union[int, float]=1
):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self._running_monitors[monitor_name] = True

        try:
            loop.run_until_complete(
                self._update_background_monitor(
                    monitor_name,
                    interval_sec=interval_sec
                )
            )

        except Exception:
            self._running_monitors[monitor_name] = False
            raise RuntimeError()

    async def stop_background_monitor(
        self,
        monitor_name: str
    ):
        self._running_monitors[monitor_name] = False

        if not self._background_monitors[monitor_name].cancelled():
            await self._background_monitors[monitor_name]

        if self.active.get(monitor_name):
            self.collected[monitor_name] = self.active[monitor_name]

    def close(self):
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)