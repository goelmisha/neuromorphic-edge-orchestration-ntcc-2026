import redis
import json
import numpy as np
import torch
from lava.proc.lif.process import LIF
from lava.proc.io.injector import SpikeInjector
from lava.proc.io.sink import RingBufferSink
from lava.magma.core.run_conditions import RunSteps
from lava.magma.core.run_configs import Loihi1SimCfg

# Connect to Redis using its Docker Compose network IP
try:
    r = redis.Redis(host='10.0.0.5', port=6379, decode_responses=True)
except Exception as e:
    print("Redis broker unreachable for SNN workload.")
    exit(1)

pubsub = r.pubsub()
pubsub.subscribe('snn_telemetry')

# The number of neurons in the LIF layer, matching the input spike dimension from test_spike.py
num_neurons = 15

print(f"Lava SNN workload initialized ({num_neurons} LIF neurons). Waiting for spike telemetry...")

# Main loop to listen for Redis messages and drive the SNN
for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        input_spikes_list = data['spikes']
        timestep = data['timestep']

        # Instantiate LIF layer
        # For simplicity in this streaming example, we re-instantiate the network
        # for each input packet. In a real-time, high-performance setting,
        # the network would be instantiated once and its state managed.
        snn_core = LIF(shape=(num_neurons,), vth=10, dv=0.9, du=0.9)

        # Create input injector and output sink for this step
        input_injector = SpikeInjector(shape=(num_neurons,))
        output_sink = RingBufferSink(shape=(num_neurons,), buffer_size=1)

        # Connect them
        input_injector.out.connect(snn_core.in_ports.s_in)
        snn_core.out.connect(output_sink.in_ports.a_in)

        # Provide input spikes to the injector. Lava expects torch.Tensor.
        # Add a batch dimension (unsqueeze(0)) as SpikeInjector often expects batched input.
        input_tensor = torch.tensor(input_spikes_list, dtype=torch.uint8).unsqueeze(0)
        input_injector.spike.set(input_tensor)

        # Run the network for one step
        snn_core.run(condition=RunSteps(num_steps=1), run_cfg=Loihi1SimCfg())

        # Get output spikes from the sink
        # deq() returns a tensor of shape (buffer_size, shape_of_sink)
        output_spikes_tensor = output_sink.deq()
        
        snn_output_spikes = [0] * num_neurons
        if output_spikes_tensor is not None and output_spikes_tensor.shape[0] > 0:
            # Extract spikes from the first (and only) step
            snn_output_spikes = output_spikes_tensor[0].tolist()

        # Stop the network after processing the step to clean up resources
        snn_core.stop()

        # Publish the SNN's output spikes to a new telemetry channel
        payload = {
            "timestep": timestep,
            "spikes": snn_output_spikes,
            "snn_type": "LIF"
        }
        r.publish('snn_output_telemetry', json.dumps(payload))
        # print(f"Timestep {timestep}: SNN output spikes published: {snn_output_spikes}")
