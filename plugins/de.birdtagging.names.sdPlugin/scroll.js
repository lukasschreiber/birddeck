/* Shared with the dependency-free Node tests. Distances use physical 72px units. */
(function (root) {
  function displayName(text) {
    return String(text || '').replace(/-(?=\p{Ll})/gu, '');
  }
  function offset(elapsed, period, stops = []) {
    if (period <= 0) return 0;
    const pause = 2000;
    const travel = period / 24 * 1000;
    let phase = elapsed % ((stops.length + 1) * pause + travel);
    const positions = [0, ...stops, period];
    for (let i = 0; i < positions.length - 1; i++) {
      if (phase <= pause) return positions[i];
      phase -= pause;
      const duration = (positions[i + 1] - positions[i]) / 24 * 1000;
      if (phase < duration) return positions[i] + phase / 1000 * 24;
      phase -= duration;
    }
    return 0;
  }
  const api = {displayName, offset};
  if (typeof module !== 'undefined') module.exports = api;
  else root.BirdScroll = api;
})(globalThis);
