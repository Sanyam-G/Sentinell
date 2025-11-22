#!/usr/bin/env python3
"""
Sentinell Chaos Engine - Intentionally break the victim cluster for demo purposes.
"""
import typer
import docker
import time
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from typing import Optional

app = typer.Typer(help="Sentinell Chaos Engine - Break things on purpose! 💥")
console = Console()


@app.command()
def break_config(
    config_path: str = typer.Option(
        "./victim/nginx/nginx.conf",
        help="Path to nginx.conf file"
    )
):
    """
    Inject a syntax error into nginx.conf and reload nginx.

    This simulates a bad config push that causes 502 errors.
    """
    console.print(Panel.fit(
        "[bold red]🔥 CHAOS: Breaking Nginx Config[/bold red]",
        border_style="red"
    ))

    config = Path(config_path)

    if not config.exists():
        console.print(f"[red]Error: Config file not found at {config_path}[/red]")
        raise typer.Exit(1)

    # Backup original
    backup_path = config.with_suffix('.conf.backup')
    content = config.read_text()
    backup_path.write_text(content)
    console.print(f"[yellow]📦 Backed up original to {backup_path}[/yellow]")

    # Inject typo - remove semicolon from a line
    broken_content = content.replace("worker_connections 1024;", "worker_connections 1024")
    config.write_text(broken_content)
    console.print("[red]💥 Injected syntax error: Removed semicolon from 'worker_connections'[/red]")

    # Reload nginx
    try:
        client = docker.from_env()
        nginx_container = client.containers.get("sentinell-nginx")

        console.print("[yellow]🔄 Attempting nginx reload...[/yellow]")
        result = nginx_container.exec_run("nginx -s reload")

        if result.exit_code != 0:
            console.print(f"[red]✗ Nginx reload failed (as expected)![/red]")
            console.print(f"[dim]{result.output.decode()}[/dim]")
        else:
            console.print("[green]✓ Nginx reloaded (unexpected - typo might not have worked)[/green]")

    except docker.errors.NotFound:
        console.print("[yellow]⚠ Nginx container not found. Config corrupted but not reloaded.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    console.print("\n[bold green]💡 To fix:[/bold green]")
    console.print(f"   cp {backup_path} {config_path}")
    console.print("   docker-compose restart nginx")


@app.command()
def leak_memory(
    container_name: str = typer.Option(
        "sentinell-product-api",
        help="Container to leak memory in"
    ),
    size_mb: int = typer.Option(
        500,
        help="Amount of memory to leak (MB)"
    )
):
    """
    Inject a memory leak into a running container.

    Creates a Python process that rapidly allocates memory.
    """
    console.print(Panel.fit(
        "[bold red]🔥 CHAOS: Memory Leak Attack[/bold red]",
        border_style="red"
    ))

    leak_script = f"""
import sys
leak = []
try:
    for i in range({size_mb}):
        leak.append(' ' * (1024 * 1024))  # 1MB chunks
        if i % 50 == 0:
            print(f'Leaked {{i}} MB...', flush=True)
    print('Leak complete. Holding memory...', flush=True)
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Leak interrupted', flush=True)
    sys.exit(0)
"""

    try:
        client = docker.from_env()
        container = client.containers.get(container_name)

        console.print(f"[yellow]📦 Target: {container_name}[/yellow]")
        console.print(f"[yellow]💾 Leaking {size_mb} MB of memory...[/yellow]")

        # Execute leak script in container
        exec_id = container.client.api.exec_create(
            container.id,
            cmd=["python3", "-c", leak_script],
            stdout=True,
            stderr=True,
        )

        console.print("[red]💥 Memory leak started in background![/red]")
        console.print(f"[dim]Exec ID: {exec_id['Id'][:12]}[/dim]")

        # Start the exec in detached mode
        container.client.api.exec_start(exec_id['Id'], detach=True)

        console.print("\n[bold green]💡 To monitor:[/bold green]")
        console.print(f"   docker stats {container_name}")
        console.print("\n[bold green]💡 To fix:[/bold green]")
        console.print(f"   docker-compose restart {container_name.replace('sentinell-', '')}")

    except docker.errors.NotFound:
        console.print(f"[red]Error: Container '{container_name}' not found[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def block_port(
    port: int = typer.Option(5432, help="Port to block"),
    duration: int = typer.Option(60, help="How long to block (seconds)")
):
    """
    Block a port by starting a process that binds to it.

    Simulates a port conflict preventing the database from starting.
    """
    console.print(Panel.fit(
        "[bold red]🔥 CHAOS: Port Blocker[/bold red]",
        border_style="red"
    ))

    blocker_script = f"""
import socket
import time
import sys

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', {port}))
    s.listen(1)
    print(f'✓ Blocking port {port}', flush=True)
    time.sleep({duration})
    print(f'Port block expired after {duration}s', flush=True)
except Exception as e:
    print(f'Error: {{e}}', flush=True)
    sys.exit(1)
finally:
    s.close()
"""

    console.print(f"[yellow]🚫 Blocking port {port} for {duration} seconds...[/yellow]")
    console.print(f"[red]💥 This will prevent PostgreSQL from binding to port {port}[/red]")

    # For port blocking, we need to run on the host or in a container with host networking
    # Let's run it on host for simplicity
    console.print("\n[bold yellow]⚠ Note:[/bold yellow]")
    console.print("   This scenario requires stopping PostgreSQL first, then blocking the port.")
    console.print("\n[bold green]💡 To execute:[/bold green]")
    console.print("   1. docker-compose stop postgres")
    console.print(f"   2. python3 -c '{blocker_script.strip()}' &")
    console.print("   3. docker-compose up -d postgres  # Will fail")
    console.print("   4. Kill the blocker process")
    console.print("   5. docker-compose up -d postgres  # Will succeed")

    # Ask if user wants to execute
    execute = typer.confirm("\nExecute the port block now?")
    if execute:
        import subprocess
        import threading

        def run_blocker():
            try:
                subprocess.run(["python3", "-c", blocker_script], check=True)
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Blocker failed: {e}[/red]")

        thread = threading.Thread(target=run_blocker, daemon=True)
        thread.start()

        console.print(f"[green]✓ Port {port} is now blocked![/green]")
        console.print("[yellow]⏰ Blocking for {duration} seconds...[/yellow]")
        console.print("\n[dim]Press Ctrl+C to stop early[/dim]")

        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            console.print("\n[yellow]Port block interrupted[/yellow]")


@app.command()
def restore():
    """
    Restore all services to healthy state.

    Fixes all chaos scenarios.
    """
    console.print(Panel.fit(
        "[bold green]🔧 RESTORE: Fixing Everything[/bold green]",
        border_style="green"
    ))

    # Restore nginx config
    backup_path = Path("./victim/nginx/nginx.conf.backup")
    config_path = Path("./victim/nginx/nginx.conf")

    if backup_path.exists():
        config_path.write_text(backup_path.read_text())
        console.print("[green]✓ Restored nginx.conf[/green]")

    # Restart all services
    console.print("[yellow]🔄 Restarting all services...[/yellow]")
    try:
        import subprocess
        subprocess.run(["docker-compose", "restart"], check=True)
        console.print("[green]✓ All services restarted[/green]")
    except subprocess.CalledProcessError:
        console.print("[red]✗ Failed to restart services[/red]")
        console.print("[yellow]Run manually: docker-compose restart[/yellow]")


@app.command()
def status():
    """
    Show current status of all victim services.
    """
    console.print(Panel.fit(
        "[bold blue]📊 Victim Cluster Status[/bold blue]",
        border_style="blue"
    ))

    try:
        client = docker.from_env()

        services = [
            "sentinell-frontend",
            "sentinell-product-api",
            "sentinell-payment-service",
            "sentinell-postgres",
            "sentinell-nginx"
        ]

        for service in services:
            try:
                container = client.containers.get(service)
                status = container.status
                health = container.attrs.get('State', {}).get('Health', {}).get('Status', 'N/A')

                status_color = "green" if status == "running" else "red"
                health_icon = "✓" if health == "healthy" or health == "N/A" else "✗"

                console.print(f"[{status_color}]{health_icon}[/{status_color}] {service:30} [{status_color}]{status}[/{status_color}] | Health: {health}")

            except docker.errors.NotFound:
                console.print(f"[red]✗[/red] {service:30} [red]not found[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
