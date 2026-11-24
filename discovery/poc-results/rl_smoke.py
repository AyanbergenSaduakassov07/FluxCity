"""sumo-rl smoke: bundled single-intersection env, 200 random steps."""
import sumo_rl, os, numpy as np
d = os.path.dirname(sumo_rl.__file__) + "/nets/single-intersection/"
env = sumo_rl.SumoEnvironment(net_file=d+"single-intersection.net.xml", route_file=d+"single-intersection.rou.xml", use_gui=False, num_seconds=2000, single_agent=True, sumo_seed=1)
obs, _ = env.reset(); tot = 0
for _ in range(200):
    obs, r, term, trunc, info = env.step(env.action_space.sample()); tot += r
    if term or trunc: break
print("obs_dim", obs.shape, "actions", env.action_space, "reward_sum", round(tot,2), "info_keys", sorted(info)[:8]); env.close()
