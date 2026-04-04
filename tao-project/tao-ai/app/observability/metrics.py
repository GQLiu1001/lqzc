"""提供与指标相关的实现。"""

from __future__ import annotations

import asyncio
import gc
import logging
import os
import resource
import time
import tracemalloc
from dataclasses import dataclass
from threading import Lock
from typing import Any

try:
    import psutil
except Exception:  # pragma: no cover - optional runtime fallback
    psutil = None  # type: ignore[assignment]

from prometheus_client import Counter, Gauge, Histogram

from app.config import settings


logger = logging.getLogger(__name__)


@dataclass
class _TaskRuntime:
    """内存中的任务运行快照。

    Prometheus 指标只负责统计数值；
    但为了识别“卡住的任务”和“疑似死循环任务”，
    系统还需要在内存里暂存每个任务最近一次活跃时间、步数等运行态信息。
    """
    started_at: float
    last_activity_at: float
    steps: int = 0
    route_source: str = "unknown"
    agent: str = "unknown"
    skill: str = "unknown"
    loop_reported: bool = False
    stuck_reported: bool = False


class MetricsManager:
    """Prometheus 指标管理器。

    这里不只是简单地“记几个计数器”，还额外承担了运行时健康巡检：
    - 统计 HTTP、工作流、检索、工具调用指标
    - 监测任务是否卡住
    - 监测是否疑似循环
    - 采样进程内存、线程数、GC、事件循环延迟
    """
    def __init__(self) -> None:
        """创建所有指标对象，并准备后台监控状态。"""
        self.enabled = settings.enable_metrics
        self._lock = Lock()
        self._tasks: dict[str, _TaskRuntime] = {}
        self._monitor_task: asyncio.Task | None = None
        self._monitor_running = False
        self._process = psutil.Process(os.getpid()) if psutil is not None else None

        # HTTP 指标：看接口流量和耗时。
        self.http_requests_total = Counter(
            "taoai_http_requests_total",
            "HTTP request count",
            labelnames=("method", "path", "status"),
        )
        self.http_request_duration = Histogram(
            "taoai_http_request_duration_seconds",
            "HTTP request latency in seconds",
            labelnames=("method", "path"),
            buckets=(0.005, 0.01, 0.03, 0.05, 0.1, 0.3, 0.5, 1, 2, 5, 10, 30),
        )

        # 任务/工作流指标：看任务生命周期、节点耗时、状态流转。
        self.tasks_inflight = Gauge(
            "taoai_tasks_inflight",
            "Number of currently running agent tasks",
        )
        self.tasks_started_total = Counter(
            "taoai_tasks_started_total",
            "Started tasks",
            labelnames=("agent", "skill", "route_source"),
        )
        self.tasks_finished_total = Counter(
            "taoai_tasks_finished_total",
            "Finished tasks",
            labelnames=("agent", "skill", "status"),
        )
        self.task_duration = Histogram(
            "taoai_task_duration_seconds",
            "End-to-end task duration in seconds",
            labelnames=("agent", "skill", "status"),
            buckets=(0.05, 0.1, 0.3, 0.5, 1, 2, 5, 10, 20, 40, 80, 160),
        )
        self.task_status_transition_total = Counter(
            "taoai_task_status_transition_total",
            "Task status transitions",
            labelnames=("from_status", "to_status", "agent", "skill"),
        )
        self.workflow_node_total = Counter(
            "taoai_workflow_node_total",
            "Workflow node events",
            labelnames=("workflow", "node", "event"),
        )
        self.workflow_node_duration = Histogram(
            "taoai_workflow_node_duration_seconds",
            "Workflow node latency in seconds",
            labelnames=("workflow", "node"),
            buckets=(0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30),
        )
        self.subworkflow_dispatch_total = Counter(
            "taoai_subworkflow_dispatch_total",
            "Supervisor handoff to subworkflows",
            labelnames=("target", "status"),
        )
        self.subworkflow_dispatch_duration = Histogram(
            "taoai_subworkflow_dispatch_duration_seconds",
            "Subworkflow dispatch duration in seconds",
            labelnames=("target", "status"),
            buckets=(0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 60),
        )
        self.task_stuck_gauge = Gauge(
            "taoai_tasks_stuck",
            "Tasks with no activity beyond threshold",
        )
        self.task_stuck_total = Counter(
            "taoai_task_stuck_total",
            "Total number of times a task was marked as stuck",
        )
        self.task_loop_suspect_total = Counter(
            "taoai_task_loop_suspect_total",
            "Tasks that exceeded configured step threshold",
        )

        # 检索/工具指标：看 RAG 命中数、工具调用成功率与延迟。
        self.retrieval_requests_total = Counter(
            "taoai_retrieval_requests_total",
            "Retrieval request count",
            labelnames=("workflow", "domain", "collection"),
        )
        self.retrieval_hits = Histogram(
            "taoai_retrieval_hits",
            "Number of retrieved hits",
            labelnames=("workflow", "domain", "collection"),
            buckets=(0, 1, 2, 3, 5, 8, 13, 21, 34),
        )
        self.tool_calls_total = Counter(
            "taoai_tool_calls_total",
            "Tool call count",
            labelnames=("tool", "status"),
        )
        self.tool_call_duration = Histogram(
            "taoai_tool_call_duration_seconds",
            "Tool call latency in seconds",
            labelnames=("tool", "status"),
            buckets=(0.005, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30),
        )

        # 运行时健康指标：主要用于排查内存泄漏、死循环、事件循环卡顿。
        self.process_rss_bytes = Gauge(
            "taoai_process_resident_memory_bytes",
            "Resident memory size in bytes",
        )
        self.process_thread_count = Gauge(
            "taoai_process_thread_count",
            "Process thread count",
        )
        self.python_gc_objects = Gauge(
            "taoai_python_gc_objects",
            "GC tracked object count",
        )
        self.python_gc_generation = Gauge(
            "taoai_python_gc_generation_count",
            "GC generation counters",
            labelnames=("generation",),
        )
        self.python_tracemalloc_bytes = Gauge(
            "taoai_python_tracemalloc_bytes",
            "Tracemalloc memory bytes",
            labelnames=("type",),
        )
        self.event_loop_lag_seconds = Gauge(
            "taoai_event_loop_lag_seconds",
            "Event loop lag in seconds",
        )

        if self.enabled and not tracemalloc.is_tracing():
            tracemalloc.start(25)

    @staticmethod
    def normalize_http_path(path: str) -> str:
        """把动态路径归一化，避免指标标签爆炸。

        例如 `/tasks/123` 和 `/tasks/456` 不应该被当成两条不同接口指标。
        """
        if path.startswith("/tasks/") and path != "/tasks/approve":
            return "/tasks/{task_id}"
        if path.startswith("/sessions/"):
            return "/sessions/{session_id}"
        return path

    def observe_http(self, *, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        """记录observeHTTP相关指标，方便排查和监控。"""
        if not self.enabled:
            return
        normalized_path = self.normalize_http_path(path)
        self.http_requests_total.labels(method, normalized_path, str(status_code)).inc()
        self.http_request_duration.labels(method, normalized_path).observe(max(0.0, duration_seconds))

    def on_task_created(self, *, task_id: str) -> None:
        """登记一个新任务进入内存追踪表。"""
        if not self.enabled:
            return
        now = time.perf_counter()
        with self._lock:
            self._tasks[task_id] = _TaskRuntime(started_at=now, last_activity_at=now)
        self.tasks_inflight.inc()

    def on_task_routed(self, *, task_id: str, agent: str, skill: str, route_source: str) -> None:
        """在任务完成路由后补全 agent/skill/source 等关键信息。"""
        if not self.enabled:
            return
        with self._lock:
            runtime = self._tasks.get(task_id)
            if runtime is None:
                runtime = _TaskRuntime(started_at=time.perf_counter(), last_activity_at=time.perf_counter())
                self._tasks[task_id] = runtime
                self.tasks_inflight.inc()
            runtime.agent = agent or "unknown"
            runtime.skill = skill or "unknown"
            runtime.route_source = route_source or "unknown"
            runtime.last_activity_at = time.perf_counter()
        self.tasks_started_total.labels(runtime.agent, runtime.skill, runtime.route_source).inc()

    def on_task_step(self, *, task_id: str, workflow: str, node: str) -> None:
        """记录任务进入某个工作流节点。

        这里除了记指标，还会：
        - 步数加一
        - 刷新最近活跃时间
        - 检查是否超过循环阈值
        """
        if not self.enabled:
            return
        self.workflow_node_total.labels(workflow, node, "enter").inc()
        with self._lock:
            runtime = self._tasks.get(task_id)
            if runtime is None:
                now = time.perf_counter()
                runtime = _TaskRuntime(started_at=now, last_activity_at=now)
                self._tasks[task_id] = runtime
                self.tasks_inflight.inc()
            runtime.steps += 1
            runtime.last_activity_at = time.perf_counter()
            if runtime.steps > settings.metrics_task_loop_step_threshold and not runtime.loop_reported:
                runtime.loop_reported = True
                self.task_loop_suspect_total.inc()
                logger.warning(
                    "metrics.loop_suspect task_id=%s steps=%s threshold=%s",
                    task_id,
                    runtime.steps,
                    settings.metrics_task_loop_step_threshold,
                )

    def observe_node_duration(self, *, workflow: str, node: str, duration_seconds: float, success: bool) -> None:
        """记录工作流节点耗时和成功/失败结果。"""
        if not self.enabled:
            return
        self.workflow_node_duration.labels(workflow, node).observe(max(0.0, duration_seconds))
        self.workflow_node_total.labels(workflow, node, "success" if success else "error").inc()

    def record_task_transition(
        self,
        *,
        from_status: str,
        to_status: str,
        agent: str,
        skill: str,
    ) -> None:
        """记录任务状态流转次数。"""
        if not self.enabled:
            return
        self.task_status_transition_total.labels(
            from_status or "UNKNOWN",
            to_status or "UNKNOWN",
            agent or "unknown",
            skill or "unknown",
        ).inc()

    def on_task_finished(self, *, task_id: str, status: str) -> None:
        """在任务结束时收口内存追踪，并上报总耗时。"""
        if not self.enabled:
            return
        runtime: _TaskRuntime | None = None
        with self._lock:
            runtime = self._tasks.pop(task_id, None)
        if runtime is None:
            return
        self.tasks_inflight.dec()
        elapsed = max(0.0, time.perf_counter() - runtime.started_at)
        final_status = status or "UNKNOWN"
        self.tasks_finished_total.labels(runtime.agent, runtime.skill, final_status).inc()
        self.task_duration.labels(runtime.agent, runtime.skill, final_status).observe(elapsed)

    def observe_subworkflow_dispatch(self, *, target: str, status: str, duration_seconds: float) -> None:
        """记录总控向子工作流分发任务的耗时与结果。"""
        if not self.enabled:
            return
        target_label = target or "unknown"
        status_label = status or "UNKNOWN"
        self.subworkflow_dispatch_total.labels(target_label, status_label).inc()
        self.subworkflow_dispatch_duration.labels(target_label, status_label).observe(max(0.0, duration_seconds))

    def observe_retrieval(self, *, workflow: str, domain: str, collection: str, hits: int) -> None:
        """记录一次检索请求和命中条数。"""
        if not self.enabled:
            return
        workflow_name = workflow or "unknown"
        domain_name = domain or "unknown"
        collection_name = collection or "unknown"
        self.retrieval_requests_total.labels(workflow_name, domain_name, collection_name).inc()
        self.retrieval_hits.labels(workflow_name, domain_name, collection_name).observe(max(0, hits))

    def observe_tool_call(self, *, tool_name: str, status: str, duration_seconds: float) -> None:
        """记录一次工具调用的状态和耗时。"""
        if not self.enabled:
            return
        tool = tool_name or "unknown"
        status_label = status or "UNKNOWN"
        self.tool_calls_total.labels(tool, status_label).inc()
        self.tool_call_duration.labels(tool, status_label).observe(max(0.0, duration_seconds))

    async def startup(self) -> None:
        """启动后台监控循环。"""
        if not self.enabled or self._monitor_running:
            return
        self._monitor_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="taoai-metrics-monitor")
        logger.info(
            "metrics.monitor.started interval=%ss stuck_threshold=%ss loop_threshold=%s",
            settings.metrics_collect_interval_seconds,
            settings.metrics_task_stuck_seconds,
            settings.metrics_task_loop_step_threshold,
        )

    async def shutdown(self) -> None:
        """优雅关闭后台监控循环。"""
        if not self.enabled:
            return
        self._monitor_running = False
        task = self._monitor_task
        if task is not None:
            try:
                await task
            except Exception:
                logger.exception("metrics.monitor.shutdown_error")
        self._monitor_task = None
        logger.info("metrics.monitor.stopped")

    async def _monitor_loop(self) -> None:
        """周期性采样运行时健康数据。

        这是一个后台循环，会固定间隔做两件事：
        - 采样进程/GC/事件循环指标
        - 扫描任务是否长时间无活动
        """
        interval = max(1, settings.metrics_collect_interval_seconds)
        expected_next = time.perf_counter() + interval
        while self._monitor_running:
            await asyncio.sleep(interval)
            now = time.perf_counter()
            lag = max(0.0, now - expected_next)
            expected_next = now + interval
            self.event_loop_lag_seconds.set(lag)

            self._sample_process_metrics()
            self._scan_stuck_tasks(now)

    def _sample_process_metrics(self) -> None:
        """采样进程层面的健康指标。"""
        gc_counts = gc.get_count()
        self.python_gc_objects.set(len(gc.get_objects()))
        self.python_gc_generation.labels("0").set(gc_counts[0])
        self.python_gc_generation.labels("1").set(gc_counts[1])
        self.python_gc_generation.labels("2").set(gc_counts[2])

        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            self.python_tracemalloc_bytes.labels("current").set(current)
            self.python_tracemalloc_bytes.labels("peak").set(peak)

        if self._process is not None:
            try:
                mem = self._process.memory_info().rss
                threads = self._process.num_threads()
                self.process_rss_bytes.set(mem)
                self.process_thread_count.set(threads)
            except Exception:
                logger.debug("metrics.process.sample_failed", exc_info=True)
        else:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # 不同系统对 ru_maxrss 的单位定义不一样，所以这里做一个近似兼容换算。
            rss_raw = float(usage.ru_maxrss)
            rss_bytes = rss_raw if rss_raw > 10_000_000 else rss_raw * 1024.0
            self.process_rss_bytes.set(rss_bytes)

    def _scan_stuck_tasks(self, now: float) -> None:
        """扫描长时间无活动的任务，并标记卡住/清理过期项。"""
        stuck_count = 0
        expired: list[str] = []
        with self._lock:
            for task_id, runtime in self._tasks.items():
                idle_for = now - runtime.last_activity_at
                if idle_for > settings.metrics_task_stuck_seconds:
                    stuck_count += 1
                    if not runtime.stuck_reported:
                        runtime.stuck_reported = True
                        self.task_stuck_total.inc()
                        logger.warning(
                            "metrics.task_stuck task_id=%s idle_seconds=%.2f threshold=%s",
                            task_id,
                            idle_for,
                            settings.metrics_task_stuck_seconds,
                        )
                # 为了避免某些异常任务永远挂在内存追踪表里，这里会做超时驱逐。
                if idle_for > settings.metrics_task_stuck_seconds * 10:
                    expired.append(task_id)
                else:
                    runtime.stuck_reported = False
            for task_id in expired:
                self._tasks.pop(task_id, None)
                self.tasks_inflight.dec()
                logger.warning("metrics.task_tracker_evicted task_id=%s", task_id)
        self.task_stuck_gauge.set(stuck_count)


metrics = MetricsManager()
