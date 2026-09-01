/**
 * Date helpers.
 *
 * Everything the API exchanges is a plain `YYYY-MM-DD` calendar day, never
 * an instant, so these deliberately work in *local* time. `toISODate` is
 * hand-rolled rather than `toISOString().slice(0, 10)` because that
 * converts to UTC first, which silently shifts the day for anyone east or
 * west of Greenwich -- a check-in made at 9pm in Delhi would be filed under
 * tomorrow.
 */

export function toISODate(value) {
  const d = value instanceof Date ? value : new Date(value);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${month}-${day}`;
}

export function todayISO() {
  return toISODate(new Date());
}

/** Shifts an ISO day by whole days, staying in local time. */
export function shiftISODate(iso, days) {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d + days);
  return toISODate(date);
}

/** The last `count` days ending today, oldest first. */
export function lastNDays(count) {
  const today = todayISO();
  return Array.from({ length: count }, (_, i) => shiftISODate(today, i - (count - 1)));
}

/** Parses an ISO day into a local Date, avoiding the UTC-midnight trap. */
export function parseISODate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

/** "12 Aug" — compact enough for axis labels and list rows. */
export function formatDay(iso) {
  return parseISODate(iso).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
  });
}

/** "Tuesday, 12 August" — for a page that is about one specific day. */
export function formatLongDay(iso) {
  return parseISODate(iso).toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
}

/** Timestamps (journal entries) are real instants, so these parse normally. */
export function formatTimestamp(value) {
  return new Date(value).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function relativeDayLabel(iso) {
  const today = todayISO();
  if (iso === today) return 'Today';
  if (iso === shiftISODate(today, -1)) return 'Yesterday';
  return formatLongDay(iso);
}
