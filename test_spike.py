import numpy as np
import redis
import json
import time

# Connect to the Alpine Redis Container
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception as e:
    print("Redis broker unreachable.")
    exit(1)

def normalize_vector(v):
    """Min-Max Probability Bounding (Eq. 11)"""
    v_min, v_max = np.min(v), np.max(v)
    epsilon = 1e-8
    return (v - v_min) / (v_max - v_min + epsilon)

def run_simulation(horizon_ms=1000):
    """Generates rate-based Poisson spikes and publishes telemetry."""
    print("Starting Text-to-Spike Ingestion Pipeline...")
    
    # Synthetic 768-dimensional dense vector (e.g., BERT embedding)
    synthetic_embedding = np.random.randn(768)
    p = normalize_vector(synthetic_embedding)
    
    f_max = 1000 # Max firing rate (Hz)
    delta_t = 0.001 # 1 ms timestep
    
    for t in range(horizon_ms):
        # Bernoulli trial for Poisson spike emission (Eq. 12)
        random_matrix = np.random.rand(768)
        spike_tensor = (random_matrix < (p * f_max * delta_t)).astype(int)
        
        # Serialize and transmit telemetry to Redis
        payload = {
            "timestep": t,
            "spikes": spike_tensor.tolist()[:15], # Truncated for dashboard visibility
            "p99_latency_ms": np.random.uniform(0.5, 1.2) # Simulated mesh latency
        }
        
        r.publish('snn_telemetry', json.dumps(payload))
        time.sleep(0.03) # Throttle to sync with real-time UI

if __name__ == "__main__":
    run_simulation()
