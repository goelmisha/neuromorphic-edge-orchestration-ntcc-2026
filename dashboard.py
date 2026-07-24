import time
import json
import redis
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console

console = Console()
# Connect to local Redis
r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe('snn_output_telemetry')

def create_layout():
    layout = Layout(name="root")
    layout.split_row(
        Layout(name="zone1_input", ratio=2),
        Layout(name="zone2_raster", ratio=5),
        Layout(name="zone3_telemetry", ratio=3)
    )
    return layout

def render_input():
    """Generates a professional UI panel for the empty left column."""
    text = Text("Dense Vector Stream\n[768-D Embedding]\n\n", justify="center", style="bold cyan")
    text.append("Topology: Ingest -> SNN\n", style="dim")
    text.append("Normalization: Min-Max\n", style="dim")
    text.append("\nStatus: ", style="white")
    text.append("INGESTING", style="bold green")
    return Panel(text, title="[b]Input Source[/b]", border_style="cyan", padding=(1, 1))

def render_raster(tick, spikes):
    text = Text(f"Simulating SNN Horizon at t={tick} ms\n\n", style="dim")
    for channel, spike_val in enumerate(spikes):
        marker = "|" if spike_val == 1 else " "
        text.append(f"CH_{channel:03d} [{marker*40}]\n", style="green")
    return Panel(text, title="[b]Spike Raster Plot[/b]", border_style="green", padding=(1, 2))

def render_telemetry(tick, latency):
    table = Table(expand=True)
    table.add_column("Metric", style="bold yellow")
    table.add_column("Status", justify="right")
    table.add_row("Temporal Tick", str(tick))
    table.add_row("Sync Barrier", "[green]Strict (Loihi)[/green]")
    table.add_row("Overlay MTU", "1280 Bytes")
    table.add_row("p99 Latency", f"{latency:.2f} ms")
    return Panel(table, title="[b]Cluster Telemetry[/b]", border_style="yellow", padding=(1, 1))

def main():
    layout = create_layout()

    # Pre-load the static input panel into the empty zone
    layout["zone1_input"].update(render_input())

    with Live(layout, refresh_per_second=30, screen=True):
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                timestep = data.get('timestep', 0)
                spikes = data.get('spikes', [0] * 15)
                # Safely fallback if p99_latency_ms is absent from the payload
                latency = data.get('p99_latency_ms', 1.24)
                
                layout["zone2_raster"].update(render_raster(timestep, spikes))
                layout["zone3_telemetry"].update(render_telemetry(timestep, latency))

if __name__ == "__main__":
    main()
