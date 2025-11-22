"""
Sentinell Observer Node - The "Nervous System"

Continuously monitors Docker containers for:
- Log streams
- Container events (die, oom, restart)
- Resource metrics

Formats everything as structured JSON for the Agent.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
import docker
from docker.models.containers import Container

logger = logging.getLogger(__name__)


class ContainerObserver:
    """Monitors Docker containers and their logs/events."""

    def __init__(self):
        # Connect to Docker using from_env() which automatically handles socket detection
        try:
            # Use from_env() - it automatically detects the Docker socket
            # and uses the proper adapter for Unix sockets
            self.client = docker.from_env()

            # Test connection
            info = self.client.info()
            logger.info(f"✓ Connected to Docker daemon (version: {info.get('ServerVersion', 'unknown')})")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise

        self.log_queues: Dict[str, asyncio.Queue] = {}
        self.event_queue = asyncio.Queue()
        self.monitored_containers: Set[str] = set()
        self.running = False

    def get_victim_containers(self) -> List[Container]:
        """Get all containers in the victim cluster."""
        try:
            all_containers = self.client.containers.list()
            victim_containers = [
                c for c in all_containers
                if c.name.startswith("sentinell-")
            ]
            return victim_containers
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    async def start(self):
        """Start monitoring all victim containers."""
        self.running = True
        logger.info("🚀 Observer starting...")

        # Start event monitor
        asyncio.create_task(self._monitor_events())

        # Start log monitors for each container
        containers = self.get_victim_containers()
        for container in containers:
            asyncio.create_task(self._monitor_container_logs(container))

        logger.info(f"✓ Monitoring {len(containers)} containers")

    async def stop(self):
        """Stop all monitoring."""
        self.running = False
        logger.info("🛑 Observer stopping...")

    async def _monitor_events(self):
        """
        Monitor Docker events for container state changes.

        Events we care about:
        - die: Container stopped
        - oom: Out of memory kill
        - restart: Container restarted
        - start: Container started
        """
        logger.info("📡 Event monitor started")

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()

            def get_events():
                return self.client.events(
                    decode=True,
                    filters={"type": "container"}
                )

            event_stream = await loop.run_in_executor(None, get_events)

            for event in event_stream:
                if not self.running:
                    break

                event_type = event.get("Action")
                container_name = event.get("Actor", {}).get("Attributes", {}).get("name")

                # Only monitor victim containers
                if not container_name or not container_name.startswith("sentinell-"):
                    continue

                # Filter for important events
                if event_type in ["die", "oom", "restart", "start", "kill", "stop"]:
                    structured_event = {
                        "type": "event",
                        "timestamp": datetime.now().isoformat(),
                        "event_type": event_type,
                        "container": container_name,
                        "status": event.get("status"),
                        "raw": event
                    }

                    await self.event_queue.put(structured_event)
                    logger.warning(f"🚨 Event: {event_type} on {container_name}")

        except Exception as e:
            logger.error(f"Event monitor error: {e}")

    async def _monitor_container_logs(self, container: Container):
        """
        Stream logs from a specific container.

        Parses logs and formats them as structured JSON.
        """
        container_name = container.name
        logger.info(f"📋 Started log monitor for {container_name}")

        # Create queue for this container
        self.log_queues[container_name] = asyncio.Queue()
        self.monitored_containers.add(container_name)

        try:
            loop = asyncio.get_event_loop()

            # Get log stream
            def get_logs():
                return container.logs(
                    stream=True,
                    follow=True,
                    timestamps=True,
                    tail=100
                )

            log_stream = await loop.run_in_executor(None, get_logs)

            for log_bytes in log_stream:
                if not self.running:
                    break

                try:
                    log_line = log_bytes.decode('utf-8').strip()

                    # Parse timestamp if present
                    timestamp = None
                    message = log_line

                    if log_line and log_line[0].isdigit():
                        parts = log_line.split(' ', 1)
                        if len(parts) == 2:
                            timestamp = parts[0]
                            message = parts[1]

                    structured_log = {
                        "type": "log",
                        "timestamp": timestamp or datetime.now().isoformat(),
                        "container": container_name,
                        "message": message,
                        "level": self._detect_log_level(message)
                    }

                    # Add to both container-specific queue and general event queue
                    await self.log_queues[container_name].put(structured_log)
                    await self.event_queue.put(structured_log)

                    # Log errors prominently
                    if structured_log["level"] in ["ERROR", "CRITICAL"]:
                        logger.warning(f"⚠️ {container_name}: {message}")

                except Exception as e:
                    logger.error(f"Error processing log from {container_name}: {e}")

        except Exception as e:
            logger.error(f"Log monitor error for {container_name}: {e}")

        finally:
            if container_name in self.monitored_containers:
                self.monitored_containers.remove(container_name)

    def _detect_log_level(self, message: str) -> str:
        """Detect log level from message content."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["error", "exception", "failed", "failure"]):
            return "ERROR"
        elif any(word in message_lower for word in ["warning", "warn"]):
            return "WARNING"
        elif any(word in message_lower for word in ["critical", "fatal"]):
            return "CRITICAL"
        elif any(word in message_lower for word in ["debug"]):
            return "DEBUG"
        else:
            return "INFO"

    async def get_container_stats(self, container_name: str) -> Optional[Dict]:
        """Get current resource usage stats for a container."""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)

            # Parse stats
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            memory_stats = stats.get("memory_stats", {})

            # Calculate CPU percentage
            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - \
                       precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0) - \
                          precpu_stats.get("system_cpu_usage", 0)

            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_count = cpu_stats.get("online_cpus", 1)
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0

            # Memory usage
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)
            memory_percent = (memory_usage / memory_limit * 100.0) if memory_limit > 0 else 0.0

            return {
                "container": container_name,
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                "memory_percent": round(memory_percent, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get stats for {container_name}: {e}")
            return None

    async def get_all_stats(self) -> List[Dict]:
        """Get stats for all monitored containers."""
        stats = []
        for container_name in self.monitored_containers:
            stat = await self.get_container_stats(container_name)
            if stat:
                stats.append(stat)
        return stats
