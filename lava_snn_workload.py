import redis
import json
import numpy as np
from lava.proc.lif.process import LIF
from lava.proc.monitor.process import Monitor
from lava.magma.core.run_conditions import RunSteps
from lava.magma.core.run_configs import Loihi1SimCfg

try:
    r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
except Exception as e:
    print(f"Redis broker unreachable for SNN workload: {e}")
    exit(1)

pubsub = r.pubsub()
pubsub.subscribe('snn_telemetry')

num_neurons = 15
print(f"Lava SNN workload initialized ({num_neurons} LIF neurons). Waiting for spike telemetry...")

for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        input_spikes_list = data['spikes']
        timestep = data['timestep']

        if len(input_spikes_list) < num_neurons:
            input_spikes_list = input_spikes_list + [0] * (num_neurons - len(input_spikes_list))
        else:
            input_spikes_list = input_spikes_list[:num_neurons]

        input_arr = np.array(input_spikes_list, dtype=float)

        # Lower threshold (vth=2) and higher bias multiplier so incoming data triggers spikes immediately
        snn_core = LIF(
            shape=(num_neurons,), 
            vth=2, 
            dv=0.5, 
            du=0.5, 
            bias_mant=(input_arr * 5).astype(int)
        )

        output_monitor = Monitor()
        output_monitor.probe(snn_core.s_out, num_steps=1)

        snn_core.run(condition=RunSteps(num_steps=1), run_cfg=Loihi1SimCfg())

        spike_data = output_monitor.get_data()
        snn_output_spikes = [0] * num_neurons
        
        try:
            proc_name = list(spike_data.keys())[0]
            port_name = list(spike_data[proc_name].keys())[0]
            step_spikes = spike_data[proc_name][port_name][0]
            snn_output_spikes = [int(s) for s in step_spikes]
        except Exception:
            pass

        snn_core.stop()

        payload = {
            "timestep": timestep,
            "spikes": snn_output_spikes,
            "snn_type": "LIF"
        }
        r.publish('snn_output_telemetry', json.dumps(payload))
