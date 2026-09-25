---
license: cc-by-4.0
pretty_name: Eidon Tracker POV IMU
size_categories:
- 100M<n<1B
task_categories:
- robotics
tags:
- egocentric
- imu
- manipulation
- motion-capture
- embodied-ai
- time-series
configs:
- config_name: default
  data_files:
  - split: train
    path: "*.parquet"
---

# Eidon Tracker POV: IMU

24 Hz orientation and motion data from a seven-point IMU harness, paired with the egocentric
video in [`eidon-ai/tracker-pov`](https://huggingface.co/datasets/eidon-ai/tracker-pov).

One row per (recording, timestamp, body slot), roughly 780 million rows. Join to the video
metadata on `recording_id`.

> ### This repo holds the sensor data only. There is no video here.
>
> The release sits in three places:
>
> | | Contents | Size |
> |---|---|---|
> | [`tracker-pov`](https://huggingface.co/datasets/eidon-ai/tracker-pov) | the 13,451 MP4s and `metadata.parquet` | 9.05 TB |
> | this repo (`tracker-pov-imu`) | the IMU streams, 779M rows, same recordings | 9.5 GB |
> | [`egocentric-pov`](https://huggingface.co/buckets/eidon-ai/egocentric-pov) | extra video with no sensor data. A bucket, so `load_dataset` does not reach it | 1.55 TB |
>
> The first two are one dataset in two pieces, joined on `recording_id`. The video is in
> `tracker-pov`, and the [organization page](https://huggingface.co/eidon-ai) has the overview.

## Schema

| Column | Type | Description |
|---|---|---|
| `recording_id` | int32 | joins to `metadata.parquet` in the video repo |
| `time_ms` | int32 | milliseconds from the start of the recording |
| `slot` | int8 | body slot, 0 to 6 |
| `quat_x`, `quat_y`, `quat_z`, `quat_w` | float32 | orientation quaternion |
| `accel_x/y/z` | float32 | accelerometer, m/s² (null on most recordings) |
| `gyro_x/y/z` | float32 | gyroscope, rad/s (null on most recordings) |
| `mag_x/y/z` | float32 | magnetometer, µT (null on most recordings) |

| Slot | Position | Slot | Position |
|---|---|---|---|
| 0 | `left_hand` | 4 | `right_forearm` |
| 1 | `left_forearm` | 5 | `right_shoulder` |
| 2 | `left_shoulder` | 6 | `chest` |
| 3 | `right_hand` | | |

The chest sensor is the natural reference frame: composing `chest⁻¹ · limb` gives torso-relative
arm pose, invariant to which way the wearer is facing.

## Usage

```python
from datasets import load_dataset
imu = load_dataset("eidon-ai/tracker-pov-imu", split="train", streaming=True)
```

Shards are written in ascending `recording_id` order and a recording is never split across two
shards, so `shard_index.json` lets you fetch one recording without scanning the set:

```python
import json, pandas as pd
from huggingface_hub import hf_hub_download

idx = json.load(open(hf_hub_download("eidon-ai/tracker-pov-imu", "shard_index.json",
                                     repo_type="dataset")))
rid = 4211
shard = next(s["shard"] for s in idx
             if s["first_recording_id"] <= rid <= s["last_recording_id"])
df = pd.read_parquet(f"hf://datasets/eidon-ai/tracker-pov-imu/{shard}",
                     filters=[("recording_id", "=", rid)])
pose = df.pivot(index="time_ms", columns="slot",
                values=["quat_x", "quat_y", "quat_z", "quat_w"])
```

## Caveats

Raw motion covers a minority of recordings. Accelerometer, gyroscope and magnetometer readings
follow a per-contributor opt-in, and 2,841 of 13,451 recordings (21.1%) carry them. Everywhere
else those columns are null, though orientation quaternions are present throughout. Filter on
`has_raw_motion` in the video repo's `metadata.parquet`.

A few recordings have an incomplete rig. 129 of 13,451 stream fewer than seven slots, sometimes
missing the chest sensor that torso-relative pose depends on. `n_slots` and `has_chest` in
`metadata.parquet` let you filter.

Timestamps are relative to the start of each recording rather than wall clock.

## Provenance, licence, citation

See the [main dataset card](https://huggingface.co/datasets/eidon-ai/tracker-pov). Published
under CC-BY-4.0 by Solidic Labs Inc (Eidon AI). For removal requests, use the contact listed on that dataset card.
