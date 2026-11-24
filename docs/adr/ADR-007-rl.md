# ADR-007: Reinforcement learning
Status: Accepted (2026-11-24)

**Decision.**
- Use `sumo-rl` (MIT) as the Gymnasium/PettingZoo environment and SB3 (MIT) for DQN and PPO.
- Subclass `sumo_rl.TrafficSignal` so that `set_next_phase` sends a `PhaseRequest` to our SafetySupervisor. sumo-rl's soft min_green is not trusted.
- Observation and reward functions use sumo-rl's plug-in registry, wrapped as named, versioned specs.
- Train with libsumo (`LIBSUMO_AS_TRACI=1`; verified on the M5). Training seeds and evaluation seeds are disjoint.
- Evaluation uses the same `Run` pipeline as every other controller, with the policy artifact referenced by hash.
- MVP scope:
  - Single intersection: DQN.
  - Corridor of up to 10 TLS: independent PPO with shared parameters.
  - MARL beyond that is deferred.
- `sumo_rl/nets/RESCO/` (CC BY-NC) is never copied, and CI blocks it. Fixture nets are regenerated with netgenerate.

**Consequences.** RL results are reported against max-pressure and actuated control on held-out seeds, and negative results are published.
