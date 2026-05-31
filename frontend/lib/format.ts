export function formatNumber(n: number) {
  return new Intl.NumberFormat(undefined).format(n);
}

export function formatPercent(n: number) {
  return `${n.toFixed(1)}%`;
}

export function formatDurationSeconds(seconds: number) {
  if (!Number.isFinite(seconds)) return "-";
  const s = Math.max(0, Math.round(seconds));
  const mm = Math.floor(s / 60);
  const ss = s % 60;
  if (mm === 0) return `${ss}s`;
  return `${mm}m ${ss}s`;
}

