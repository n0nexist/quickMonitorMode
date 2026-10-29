#!/usr/bin/env python3
import subprocess
import sys
import re
import os
import readline
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import print

console = Console()

# Quick root check
if os.getuid() != 0:
    print("[bold red]✗ run me as root.[/bold red]")
    sys.exit(-1)


def setup_tab_completion(choices):
    """Attach readline tab-completion to the given choices."""
    if readline is None:
        return

    def completer(text, state):
        matches = [c for c in choices if c.startswith(text)]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


def get_wireless_interfaces():
    """Detect wireless interfaces via sysfs."""
    interfaces = []

    if os.path.exists('/sys/class/net'):
        for iface in os.listdir('/sys/class/net'):
            if os.path.exists(f'/sys/class/net/{iface}/wireless') or \
                os.path.exists(f'/sys/class/net/{iface}/phy80211'):
                interfaces.append(iface)
    else:
        print("[bold red]✗ /sys/class/net does not exist.[/bold red]")
        sys.exit(1)

    return list(set(interfaces))


def run_cmd(cmd):
    """Execute a command and report failures."""
    try:
        subprocess.run(cmd, check=True, text=True)
        return True
    except subprocess.CalledProcessError:
        console.print(f"[bold red]✗ Command failed: {' '.join(cmd)}[/bold red]")
        return False


def main():
    console.print(Panel.fit("[bold cyan]Quick-Monitor-Mode[/bold cyan]", subtitle="///n0nexist\\\\\\"))

    # Detect interfaces
    interfaces = get_wireless_interfaces()

    if not interfaces:
        console.print("[bold red]✗ No wireless interface detected.[/bold red]")
        sys.exit(2)

    # Interface selection
    console.print(f"[green]✓[/green] Wireless interfaces found: [bold yellow]{', '.join(interfaces)}[/bold yellow]")
    setup_tab_completion(interfaces)
    iface = Prompt.ask("[yellow]Select the interface to configure[/yellow]", choices=interfaces, default=interfaces[len(interfaces) - 1])

    console.print(f"\n[bold]The following commands will run on [green]{iface}[/green]:[/bold]")
    console.print(f" 1. [cyan]ip link set {iface} down[/cyan]")
    console.print(f" 2. [cyan]iw dev {iface} set type monitor[/cyan]")
    console.print(f" 3. [cyan]ip link set {iface} up[/cyan]")
    console.print(f" 4. [cyan]iw dev {iface} info[/cyan]\n")

    if not Confirm.ask("[bold yellow]Proceed?[/bold yellow]", default=True):
        console.print("[red]Operation cancelled.[/red]")
        sys.exit(3)

    console.print("\n[bold blue]Configuring...[/bold blue]\n")

    if not run_cmd(["ip", "link", "set", iface, "down"]):
        sys.exit(4)
    console.print(f"[green]✓[/green] Interface {iface} set DOWN")

    if not run_cmd(["iw", "dev", iface, "set", "type", "monitor"]):
        console.print("[red]Make sure the adapter driver supports monitor mode![/red]")
        sys.exit(5)
    console.print(f"[green]✓[/green] Monitor mode enabled")

    if not run_cmd(["ip", "link", "set", iface, "up"]):
        sys.exit(6)
    console.print(f"[green]✓[/green] Interface {iface} set UP")

    console.print("\n[bold blue]Verification:[/bold blue]")
    subprocess.run(["iw", "dev", iface, "info"])

    console.print("\n[bold green]Done![/bold green] If [bold]type monitor[/bold] appears above, the interface is ready.\n")


if __name__ == "__main__":
    main()
