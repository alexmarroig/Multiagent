"""Container-based sandbox profile for secure tool execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ContainerSandboxProfile:
    image: str = "python:3.12-slim"
    seccomp_profile: str = "runtime/default"
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    network_isolation: bool = True


class ContainerSandbox:
    def __init__(self, profile: ContainerSandboxProfile | None = None) -> None:
        self.profile = profile or ContainerSandboxProfile()

    def runtime_args(self) -> list[str]:
        args = [
            "--security-opt",
            f"seccomp={self.profile.seccomp_profile}",
            "--cpus",
            self.profile.cpu_limit.replace("m", ""),
            "--memory",
            self.profile.memory_limit,
        ]
        if self.profile.network_isolation:
            args.extend(["--network", "none"])
        return args
