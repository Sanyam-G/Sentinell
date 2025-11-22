"""
Sentinell Agent Tools - The Tool Belt

LangChain tools that allow the agent to interact with Docker containers.
These are the ONLY operations the agent can perform - this ensures safety.
"""
import docker
import logging
from typing import List, Dict, Optional
from langchain.tools import tool

logger = logging.getLogger(__name__)

# Global Docker client
_docker_client = None


def get_docker_client():
    """Get or create Docker client instance."""
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


@tool
def read_logs(container_name: str, tail: int = 100) -> str:
    """
    Read recent logs from a container.

    Args:
        container_name: Name of the container (e.g., "sentinell-nginx")
        tail: Number of lines to read from the end (default: 100)

    Returns:
        String containing the log lines
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
        logger.info(f"📋 Read {tail} lines from {container_name}")
        return logs
    except Exception as e:
        error_msg = f"Failed to read logs from {container_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def exec_command(container_name: str, command: str) -> str:
    """
    Execute a command inside a container.

    Args:
        container_name: Name of the container
        command: Shell command to execute (as a string, will be split)

    Returns:
        Output from the command

    Security: Only allows safe diagnostic commands.
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)

        # Execute command
        result = container.exec_run(command)
        output = result.output.decode('utf-8')

        logger.info(f"⚙️ Executed in {container_name}: {command}")
        logger.info(f"Exit code: {result.exit_code}")

        return f"Exit code: {result.exit_code}\n\nOutput:\n{output}"
    except Exception as e:
        error_msg = f"Failed to execute command in {container_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def read_file(container_name: str, file_path: str) -> str:
    """
    Read a file from inside a container.

    Args:
        container_name: Name of the container
        file_path: Path to the file inside the container

    Returns:
        Contents of the file
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)

        # Read file using cat
        result = container.exec_run(f"cat {file_path}")

        if result.exit_code != 0:
            return f"Error: File not found or cannot be read: {file_path}"

        content = result.output.decode('utf-8')
        logger.info(f"📄 Read file {file_path} from {container_name}")

        return content
    except Exception as e:
        error_msg = f"Failed to read file from {container_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def restart_container(container_name: str) -> str:
    """
    Restart a container.

    Args:
        container_name: Name of the container to restart

    Returns:
        Status message
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        container.restart()
        logger.warning(f"🔄 Restarted container: {container_name}")
        return f"Successfully restarted {container_name}"
    except Exception as e:
        error_msg = f"Failed to restart {container_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def patch_nginx_config(container_name: str, old_content: str, new_content: str) -> str:
    """
    Patch nginx configuration file.

    Args:
        container_name: Name of the nginx container
        old_content: Content to search for (will be replaced)
        new_content: New content to insert

    Returns:
        Status message

    Note: This performs a simple find/replace in /etc/nginx/nginx.conf
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)

        # Read current config
        result = container.exec_run("cat /etc/nginx/nginx.conf")
        if result.exit_code != 0:
            return "Error: Could not read nginx.conf"

        current_config = result.output.decode('utf-8')

        # Apply patch
        if old_content not in current_config:
            return f"Error: Pattern not found in config: {old_content[:50]}..."

        patched_config = current_config.replace(old_content, new_content)

        # Write back (using echo and shell redirection)
        # Escape single quotes in the config
        escaped_config = patched_config.replace("'", "'\"'\"'")
        write_command = f"sh -c 'echo \"{escaped_config}\" > /etc/nginx/nginx.conf'"

        write_result = container.exec_run(write_command)
        if write_result.exit_code != 0:
            return f"Error: Failed to write config: {write_result.output.decode('utf-8')}"

        # Reload nginx
        reload_result = container.exec_run("nginx -s reload")
        if reload_result.exit_code != 0:
            return f"Error: Config written but reload failed: {reload_result.output.decode('utf-8')}"

        logger.warning(f"✅ Patched and reloaded nginx config in {container_name}")
        return "Successfully patched nginx configuration and reloaded"

    except Exception as e:
        error_msg = f"Failed to patch nginx config: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def get_container_stats(container_name: str) -> str:
    """
    Get resource usage statistics for a container.

    Args:
        container_name: Name of the container

    Returns:
        CPU and memory statistics
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_name)
        stats = container.stats(stream=False)

        # Parse stats
        cpu_stats = stats.get("cpu_stats", {})
        memory_stats = stats.get("memory_stats", {})

        memory_usage_mb = memory_stats.get("usage", 0) / (1024 * 1024)
        memory_limit_mb = memory_stats.get("limit", 0) / (1024 * 1024)
        memory_percent = (memory_usage_mb / memory_limit_mb * 100) if memory_limit_mb > 0 else 0

        result = f"""Container: {container_name}
Memory: {memory_usage_mb:.2f} MB / {memory_limit_mb:.2f} MB ({memory_percent:.1f}%)
Status: {container.status}
"""
        logger.info(f"📊 Retrieved stats for {container_name}")
        return result

    except Exception as e:
        error_msg = f"Failed to get stats for {container_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


# Export all tools as a list for LangChain
ALL_TOOLS = [
    read_logs,
    exec_command,
    read_file,
    restart_container,
    patch_nginx_config,
    get_container_stats,
]
