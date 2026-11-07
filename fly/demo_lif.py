"""Quick look at the LIF core (Phase 4A): A drives B (excitatory), B drives C (inhibitory).

Run from the project root:   .venv/bin/python -m fly.demo_lif
"""

import numpy as np

from fly.lif import LIFNetwork, load_params, synaptic_matrix

P = load_params()
ids = ["A", "B", "C"]
w = synaptic_matrix(
    [0, 1, 2], [0, 1], [1, 2], [150, 150], ["acetylcholine", "gaba"], scale_mV=P.w_syn_mV
)
net = LIFNetwork(w, P)

print(f"constants: {P}\n")
print("A gets a steady 12 mV push for 200 ms; B and C get nothing directly.\n")
spikes = {n: [] for n in ids}
v_c = []
for k in range(round(300 / P.dt_ms)):
    drive = np.array([12.0 if k * P.dt_ms < 200 else 0.0, 0.0, 0.0])
    s = net.step(drive)
    for i, n in enumerate(ids):
        if s[i]:
            spikes[n].append(round(k * P.dt_ms, 1))
    v_c.append(net.v[2])

for n in ids:
    t = spikes[n]
    print(f"{n}: {len(t):3d} spikes" + (f", first at {t[0]} ms" if t else ""))
print(f"\nC (inhibited by B) lowest voltage: {min(v_c):.2f} mV (rest is {P.v_rest_mV} mV)")
