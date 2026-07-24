import pandas as pd
import matplotlib.pyplot as plt

def generate_ieee_graphs():
    print("Loading telemetry_results.csv...")
    df = pd.read_csv('telemetry_results.csv')

    # Apply formal academic styling parameters
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 300
    })

    # Initialize a vertically stacked figure
    fig = plt.figure(figsize=(8, 11))
    
    # Graph 1: MTU Optimization Latency
    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(df['timestep_ms'], df['p99_latency_ms'], color='#003366', linewidth=1.5, alpha=0.8)
    ax1.axhline(y=1.2, color='#CC0000', linestyle='--', linewidth=1.2, label='Strict Loihi Tolerance Limit')
    ax1.set_ylabel('p99 Latency (ms)')
    ax1.set_title('Fig 1. (a) Overlay Network Jitter Mitigation (MTU=1280)')
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.legend(loc='upper right')

    # Graph 2: Poisson Encoded Spiking Activity
    ax2 = plt.subplot(3, 1, 2, sharex=ax1)
    ax2.plot(df['timestep_ms'], df['total_network_spikes'], color='#2ca02c', linewidth=1.0, alpha=0.7)
    ax2.set_xlabel('Simulation Horizon (ms)')
    ax2.set_ylabel('Global Spike Count')
    ax2.set_title('Fig 1. (b) System-Wide Poisson Activity (768-D Tensor)')
    ax2.grid(True, linestyle=':', alpha=0.7)

    # Graph 3: System Migration Phases (Logarithmic)
    ax3 = plt.subplot(3, 1, 3)
    phases = ['Checkpoint', 'Transfer', 'Restore']
    
    # Placeholder temporal data in milliseconds
    # durations = [145, 12500, 210] 
    
    durations = [21551, 38120, 17016]

    bars = ax3.bar(phases, durations, color=['#e377c2', '#17becf', '#ff7f0e'], alpha=0.8, width=0.5)
    ax3.set_yscale('log')
    ax3.set_ylabel('Duration (ms) [Log Scale]')
    ax3.set_title('Fig 3. System Migration Phases')
    ax3.grid(True, axis='y', linestyle=':', alpha=0.7)
    
    # Add data labels above bars
    for bar in bars:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, yval * 1.15, f'{yval} ms', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    output_filename = 'ieee_telemetry_graphs.png'
    plt.savefig(output_filename, format='png', dpi=300, bbox_inches='tight')
    
    print(f"Success! 3-part graph saved to {output_filename}")

if __name__ == "__main__":
    generate_ieee_graphs()
