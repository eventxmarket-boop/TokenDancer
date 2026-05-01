export function parseLaneOffsets(rawValue, fallbackOffsets = [0, 10_000, 20_000]) {
  const raw = String(rawValue ?? '').trim();
  if (!raw) {
    return fallbackOffsets.slice();
  }

  const parsed = raw
    .split(',')
    .map((part) => Number.parseInt(part.trim(), 10))
    .filter((value) => Number.isFinite(value) && value >= 0);

  return parsed.length > 0 ? parsed : fallbackOffsets.slice();
}

export async function runSerializedLaneScheduler({
  laneStartOffsetsMs = [0, 10_000, 20_000],
  laneIntervalMs = 30_000,
  stopSignals,
  onTick,
  onLaneStart,
}) {
  if (typeof onTick !== 'function') {
    throw new Error('onTick must be a function');
  }

  const offsets = Array.isArray(laneStartOffsetsMs) && laneStartOffsetsMs.length > 0
    ? laneStartOffsetsMs.slice()
    : [0, 10_000, 20_000];

  let lock = Promise.resolve();

  const acquire = async () => {
    let release = null;
    const next = new Promise((resolve) => {
      release = resolve;
    });
    const previous = lock;
    lock = next;
    await previous;
    return () => {
      release?.();
    };
  };

  const laneTasks = offsets.map((offsetMs, laneIndex) => (async () => {
    await sleep(offsetMs);
    if (stopSignals?.size) {
      return;
    }

    onLaneStart?.({ laneIndex: laneIndex + 1, offsetMs });
    let cycle = 0;

    while (!stopSignals?.size) {
      cycle += 1;
      const release = await acquire();

      try {
        await onTick({
          laneIndex: laneIndex + 1,
          cycle,
          offsetMs,
        });
      } finally {
        release();
      }

      if (stopSignals?.size) {
        break;
      }

      await sleep(laneIntervalMs);
    }
  })());

  await Promise.all(laneTasks);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
