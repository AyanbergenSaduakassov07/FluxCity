# ADR-010: Live telemetry protocol
Status: Accepted (2026-11-24)

**Decision.**
- Use a WebSocket per live run with four channels: `hello` (snapshot plus id table, sent on connect and reconnect), `frame` (binary, 10 Hz), `stats` (JSON, 1 Hz) and `event` (JSON, discrete).
- Frame layout: little-endian, struct of arrays.
  - Header: `u8 ver, u8 kind, u32 seq, f64 t, u32 n`.
  - Per-vehicle arrays: `u32 idx, f32 dx, f32 dy` (metres from the network origin), `u16 angle*100, u16 speed_cms, u8 type`.
  - TLS states are sent only on change.
  - deck.gl consumes the arrays directly through `COORDINATE_SYSTEM.METER_OFFSETS` with a lon/lat origin, so the client does no per-frame reprojection.
- The client uses a render-behind playout buffer (about 200 ms) with Hermite interpolation from heading and speed. It never extrapolates, applies a teleport-distance guard and resets on a time regress. This is the FlowState pattern, reimplemented.
- Backpressure: the server drops frames, never stats or events, when the socket buffer is above its threshold.
- Recorded playback replays parquet frames through the same protocol, so the compare view handles live and recorded runs alike.

**Consequence.** At 5k vehicles a frame is about 75 KB, or 0.75 MB/s at 10 Hz, which is fine on localhost.
