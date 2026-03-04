"""
Docker plugin for Catalyst.

Provides container lifecycle management: run, stop, logs, exec, build.
"""

import asyncio
from typing import Any, Dict, Optional, List
from core.plugin import Plugin


class DockerPlugin(Plugin):
    name = "docker"
    description = "Container lifecycle management (run, stop, logs, exec, build)"

    def __init__(self, docker_host: Optional[str] = None):
        """
        Initialize Docker plugin.

        Args:
            docker_host: Optional Docker daemon host (e.g., "unix:///var/run/docker.sock" or "tcp://localhost:2375").
        """
        super().__init__()
        self.docker_host = docker_host
        self._client = None

    def on_load(self):
        """Initialize Docker client."""
        try:
            import docker
            if self.docker_host:
                self._client = docker.DockerClient(base_url=self.docker_host)
            else:
                self._client = docker.from_env()
            # Test connection
            self._client.ping()
        except ImportError:
            raise RuntimeError("Docker Python SDK is not installed. Install with 'pip install docker'")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker daemon: {e}")

    async def on_unload(self):
        """Close Docker client."""
        if self._client:
            self._client.close()

    def health_check(self) -> bool:
        """Check if Docker daemon is reachable."""
        try:
            if self._client:
                self._client.ping()
                return True
            return False
        except Exception:
            return False

    async def execute(
        self,
        action: str,
        image: Optional[str] = None,
        command: Optional[str] = None,
        container_id: Optional[str] = None,
        dockerfile_path: Optional[str] = None,
        tag: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[int, int]] = None,
        detach: bool = True,
        remove: bool = False,
        tail: int = 100,
        **kwargs
    ) -> Any:
        """
        Execute a Docker operation.

        Args:
            action: One of "run", "stop", "logs", "exec", "build", "ps"
            image: Docker image name (for run, exec, ps)
            command: Command to run (for run, exec)
            container_id: Container ID or name (for stop, logs, exec)
            dockerfile_path: Path to Dockerfile (for build)
            tag: Image tag (for build)
            env: Environment variables dict
            volumes: Volume mappings: {host_path: container_path}
            ports: Port mappings: {container_port: host_port}
            detach: If True, run container in background (run)
            remove: If True, remove container after stop (stop)
            tail: Number of log lines to return (logs)
            **kwargs: Additional arguments passed to docker-py methods.

        Returns:
            Varies by action:
              - run: container.id
              - stop: None
              - logs: str (log output)
              - exec: output of exec command (str)
              - build: image ID(s)
              - ps: list of container info dicts
        """
        if self._client is None:
            raise RuntimeError("Docker client not initialized")

        loop = asyncio.get_event_loop()
        if action == "run":
            return await loop.run_in_executor(None, self._run, image, command, env, volumes, ports, detach, **kwargs)
        elif action == "stop":
            return await loop.run_in_executor(None, self._stop, container_id, remove, **kwargs)
        elif action == "logs":
            return await loop.run_in_executor(None, self._logs, container_id, tail, **kwargs)
        elif action == "exec":
            return await loop.run_in_executor(None, self._exec, container_id, command, **kwargs)
        elif action == "build":
            return await loop.run_in_executor(None, self._build, dockerfile_path, tag, **kwargs)
        elif action == "ps":
            return await loop.run_in_executor(None, self._list_containers, **kwargs)
        else:
            raise ValueError(f"Unsupported Docker action: {action}")

    def _run(self, image, command, env, volumes, ports, detach, **kwargs):
        run_kwargs = {"image": image, "detach": detach, "environment": env, "volumes": volumes, "ports": ports}
        run_kwargs.update(kwargs)
        if command:
            run_kwargs["command"] = command
        container = self._client.containers.run(**run_kwargs)
        return container.id

    def _stop(self, container_id, remove, **kwargs):
        container = self._client.containers.get(container_id)
        container.stop()
        if remove:
            container.remove()

    def _logs(self, container_id, tail, **kwargs):
        container = self._client.containers.get(container_id)
        logs = container.logs(tail=tail).decode('utf-8', errors='replace')
        return logs

    def _exec(self, container_id, command, **kwargs):
        container = self._client.containers.get(container_id)
        # Execute command and capture output
        exit_code, output = container.exec_run(cmd=command, demux=True, **kwargs)
        # output is tuple (stdout, stderr)
        stdout, stderr = output if output else (b'', b'')
        result = stdout.decode('utf-8', errors='replace') if stdout else ''
        if stderr:
            result += stderr.decode('utf-8', errors='replace')
        if exit_code != 0:
            raise RuntimeError(f"Docker exec returned exit code {exit_code}: {result}")
        return result

    def _build(self, dockerfile_path, tag, **kwargs):
        image, logs = self._client.images.build(path=dockerfile_path, tag=tag, **kwargs)
        return image.id

    def _list_containers(self, **kwargs):
        containers = self._client.containers.list(**kwargs)
        return [
            {
                "id": c.id[:12],
                "names": c.name,
                "image": c.image.tags,
                "status": c.status,
            }
            for c in containers
        ]
