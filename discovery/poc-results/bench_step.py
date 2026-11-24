"""Compare TraCI vs libsumo per-step cost with full vehicle-state reads (telemetry use case)."""
import sys, time, importlib
mod = importlib.import_module(sys.argv[1])
cmd = ["sumo", "-n", "out/grid.net.xml", "-r", "out/grid.rou.xml", "--seed", "42", "--no-step-log", "--end", "3600"]
mod.start(cmd)
t0 = time.perf_counter(); n = 0; peak = 0
while mod.simulation.getMinExpectedNumber() > 0:
    mod.simulationStep(); n += 1
    ids = mod.vehicle.getIDList(); peak = max(peak, len(ids))
    _ = [(mod.vehicle.getPosition(v), mod.vehicle.getAngle(v), mod.vehicle.getSpeed(v)) for v in ids]
    for tl in mod.trafficlight.getIDList(): mod.trafficlight.getRedYellowGreenState(tl)
dt = time.perf_counter() - t0; mod.close()
print(f"{sys.argv[1]}: steps={n} peak_veh={peak} wall={dt:.2f}s ms/step={1000*dt/n:.3f}")
