# LLM-Generated Code Insights

Observations from reviewing and fixing AI-generated code in this project.

## 1. Faking at the wrong seam (DHT driver)

**Problem:** The LLM created a `FakePigpio` that returned pre-baked decoded bits, bypassing `PigpioImpl` entirely. Tests passed but the actual timing-based bit decoding logic — the hard part — was completely untested. Coverage was 52%.

**Manual approach:** Fake the *hardware itself* (`pigpio.pi()`), not the hardware abstraction layer. `FakePi` implements the pigpio daemon protocol and fires callbacks with realistic tick timings when triggered. This exercises the real production code: callback registration, edge timing, bit decoding, checksum validation.

**Fix:** Dependency-inject `pi` into `PigpioHardware`, replace `FakePigpio` with `FakePi`, combine trigger+read so the callback is registered before the trigger fires. Coverage went to 92%.

**Pattern:** LLMs optimize for "tests pass" rather than "tests catch bugs." They instinctively mock at the highest seam, pushing all complexity behind an untested boundary. The better seam is lower — at the actual hardware boundary — even though it requires a more sophisticated fake.
