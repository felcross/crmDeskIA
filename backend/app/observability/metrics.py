from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricsStore:
    _requests_total: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _request_duration_seconds: list[float] = field(default_factory=list)
    _active_connections: int = 0
    _buckets: tuple[float, ...] = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def inc_request(self, method: str, path: str, status: int) -> None:
        key = f"{method}|{path}|{status}"
        self._requests_total[key] += 1

    def observe_duration(self, duration_s: float) -> None:
        self._request_duration_seconds.append(duration_s)

    def inc_active(self) -> None:
        self._active_connections += 1

    def dec_active(self) -> None:
        self._active_connections = max(0, self._active_connections - 1)

    def render(self) -> str:
        lines: list[str] = []

        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        for key, count in sorted(self._requests_total.items()):
            method, path, status = key.split("|", 2)
            lines.append(
                f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
            )

        durations = self._request_duration_seconds
        lines.append("")
        lines.append("# HELP http_request_duration_seconds Request duration in seconds")
        lines.append("# TYPE http_request_duration_seconds histogram")
        bucket_counts: dict[float, int] = {b: 0 for b in self._buckets}
        for d in durations:
            for b in self._buckets:
                if d <= b:
                    bucket_counts[b] += 1
        for b in self._buckets:
            lines.append(f'http_request_duration_seconds_bucket{{le="{b}"}} {bucket_counts[b]}')
        lines.append(f'http_request_duration_seconds_bucket{{le="+Inf"}} {len(durations)}')
        lines.append(f"http_request_duration_seconds_count {len(durations)}")
        lines.append(f"http_request_duration_seconds_sum {sum(durations):.6f}")

        lines.append("")
        lines.append("# HELP http_active_connections Current active connections")
        lines.append("# TYPE http_active_connections gauge")
        lines.append(f"http_active_connections {self._active_connections}")

        return "\n".join(lines) + "\n"


metrics = MetricsStore()
