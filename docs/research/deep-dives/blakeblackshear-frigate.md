# blakeblackshear/frigate — PATTERN-ONLY (motion-gate algorithm)

The reference NVR: cheap CPU motion detection gates expensive object detection
so the detector only runs when pixels actually changed. That gating pattern is
exactly REMY's wake-on-vision shape (frame-diff → VLM/Claude only on change).
The stack itself (go2rtc, detectors, recording, web UI) is a multi-GB appliance
REMY must not swallow.

- **Stars/health:** 34.9k, active (2026-08) · **License:** MIT

## Does better than REMY
A production-hardened motion detector that runs on a ~100px grayscale downscale
for near-zero CPU/RAM, with the failure modes already solved: auto-calibration,
contrast normalization, lighting-storm/IR-switch rejection, persistent-motion
averaging so slow scene drift doesn't re-trigger.

## Read these files
- `blakeblackshear/frigate@e73a14d:frigate/motion/improved_motion.py:L53-254` —
  the whole `detect()`: resize → percentile contrast stretch (L87-107) → mask →
  blur → `cv2.absdiff` vs running average → threshold → dilate → contours →
  boxes (L125-155); lightning/scene-change recalibration (L180-207); only
  average motion frames into the background after 10 persistent frames
  (L236-252) so a person standing still stays "motion".

## Lift
Port `detect()` minus PTZ/mask/debug into a single ~80-line REMY module:
cv2 + numpy only (swap `scipy.ndimage.gaussian_filter` for `cv2.GaussianBlur`
to skip the scipy dep). Feed it 2-5 fps grabs from the C720; emit a
`vision.motion` event on the bus; let the router decide whether to spend a
moondream call or a Claude session. numpy<2 fine.

## Avoid
Everything else: go2rtc, ffmpeg presets, TensorRT/Coral detectors, tracking,
the web UI. Also don't adopt its always-on ffmpeg decode loop — REMY should
poll frames only while a "watch" task is active.

## License constraint
MIT — a ported snippet is fine with attribution.

## Jetson cost
**ESTIMATE** <50MB RAM, a few % CPU at 2-5 fps on a 100px downscale, zero GPU.

## Effort
**S** — one file plus a capture loop.
