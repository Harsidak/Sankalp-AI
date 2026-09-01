/**
 * Check-in — one mood and energy rating per calendar day.
 *
 * The day is selectable rather than fixed to today, because a missed day is
 * the normal case and the API models a check-in as an upsert on
 * (user_id, checkin_date): posting the same day twice re-rates it instead
 * of erroring. That unique constraint is what lets this page treat "create"
 * and "edit" as the same action.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { checkinApi } from '../api/wellness';
import PageShell from '../components/layout/PageShell';
import ScoreScale from '../components/wellness/ScoreScale';
import { formatDay, lastNDays, relativeDayLabel, todayISO } from '../utils/dates';

const MOOD_LABELS = ['Rough', 'Low', 'Okay', 'Good', 'Great'];
const ENERGY_LABELS = ['Drained', 'Tired', 'Steady', 'Lively', 'Charged'];
const HISTORY_DAYS = 35;

export default function CheckIn() {
  const [day, setDay] = useState(todayISO);
  const [history, setHistory] = useState([]);
  const [streak, setStreak] = useState(null);

  const [mood, setMood] = useState(3);
  const [energy, setEnergy] = useState(3);
  const [note, setNote] = useState('');

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      const [entries, streakData] = await Promise.all([
        checkinApi.list({ days: HISTORY_DAYS }),
        checkinApi.streak(),
      ]);
      setHistory(entries);
      setStreak(streakData);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not load your check-ins.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    load();
  }, [load]);

  /** The check-in already recorded for the selected day, if there is one. */
  const existing = useMemo(
    () => history.find((c) => c.checkin_date === day) || null,
    [history, day]
  );

  useEffect(() => {
    // Switching days loads that day's answers into the form. Without this
    // the previous day's ratings would sit there looking like this day's.
    // oxlint-disable-next-line react/set-state-in-effect
    setMood(existing?.mood_score ?? 3);
    setEnergy(existing?.energy_score ?? 3);
    setNote(existing?.note ?? '');
    setSaved('');
  }, [existing, day]);

  /** Keyed by date so the calendar strip is a lookup, not a scan per cell. */
  const byDate = useMemo(
    () => Object.fromEntries(history.map((c) => [c.checkin_date, c])),
    [history]
  );

  const strip = useMemo(() => lastNDays(HISTORY_DAYS), []);

  const handleSave = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    setSaved('');
    try {
      await checkinApi.create({
        mood_score: mood,
        energy_score: energy,
        note: note.trim() || null,
        checkin_date: day,
      });
      setSaved(existing ? 'Updated.' : 'Saved.');
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not save that check-in.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!existing) return;
    setIsSaving(true);
    setError('');
    try {
      await checkinApi.remove(existing.id);
      setSaved('Removed.');
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not remove that check-in.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <PageShell
      eyebrow="Daily"
      title="How are you today?"
      subtitle={
        streak?.current_streak
          ? `${streak.current_streak} day${streak.current_streak === 1 ? '' : 's'} running · longest ${streak.longest_streak}`
          : 'One check-in starts a streak.'
      }
      actions={
        <Link to="/dashboard" className="btn btn-ghost btn-sm">
          Back to dashboard
        </Link>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      <div className="panel-row is-lopsided">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>{relativeDayLabel(day)}</h2>
              <p>{existing ? 'Already recorded — saving will re-rate it.' : 'Not recorded yet.'}</p>
            </div>
            <input
              type="date"
              className="date-input"
              value={day}
              max={todayISO()}
              onChange={(e) => setDay(e.target.value || todayISO())}
            />
          </div>

          <form onSubmit={handleSave} className="checkin-form">
            <div className="form-group">
              <label>Mood</label>
              <ScoreScale name="Mood" value={mood} labels={MOOD_LABELS} onChange={setMood} />
            </div>

            <div className="form-group">
              <label>Energy</label>
              <ScoreScale
                name="Energy"
                value={energy}
                labels={ENERGY_LABELS}
                onChange={setEnergy}
              />
            </div>

            <div className="form-group">
              <label htmlFor="note">Anything worth remembering?</label>
              <textarea
                id="note"
                value={note}
                maxLength={2000}
                placeholder="Optional. A line is enough."
                onChange={(e) => setNote(e.target.value)}
                style={{ minHeight: '96px' }}
              />
            </div>

            <div className="form-row">
              <button type="submit" className="btn btn-primary" disabled={isSaving}>
                {isSaving ? 'Saving…' : existing ? 'Update check-in' : 'Save check-in'}
              </button>
              {existing && (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={handleDelete}
                  disabled={isSaving}
                >
                  Remove
                </button>
              )}
              {saved && <span className="form-note is-good">{saved}</span>}
            </div>
          </form>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Last {HISTORY_DAYS} days</h2>
              <p>{history.length} recorded · tap a day to edit it</p>
            </div>
          </div>

          {isLoading ? (
            <div className="page-loader">
              <span className="spinner" />
            </div>
          ) : (
            <>
              <div className="day-strip">
                {strip.map((iso) => {
                  const entry = byDate[iso];
                  return (
                    <button
                      key={iso}
                      type="button"
                      title={`${formatDay(iso)}${entry ? ` · mood ${entry.mood_score}` : ' · no check-in'}`}
                      aria-label={`${formatDay(iso)}${entry ? `, mood ${entry.mood_score}` : ', no check-in'}`}
                      className={`day-cell${entry ? ' is-filled' : ''}${iso === day ? ' is-selected' : ''}`}
                      style={
                        entry ? { background: `var(--mood-${entry.mood_score})` } : undefined
                      }
                      onClick={() => setDay(iso)}
                    />
                  );
                })}
              </div>

              <div className="scale-legend">
                {MOOD_LABELS.map((label, i) => (
                  <span key={label}>
                    <i style={{ background: `var(--mood-${i + 1})` }} />
                    {label}
                  </span>
                ))}
              </div>

              {history.length ? (
                <ul className="recent-list">
                  {[...history]
                    .sort((a, b) => b.checkin_date.localeCompare(a.checkin_date))
                    .slice(0, 6)
                    .map((entry) => (
                      <li key={entry.id}>
                        <button type="button" onClick={() => setDay(entry.checkin_date)}>
                          <span
                            className="recent-dot"
                            style={{ background: `var(--mood-${entry.mood_score})` }}
                          />
                          <span className="recent-day">{formatDay(entry.checkin_date)}</span>
                          <span className="recent-note">
                            {entry.note || `Mood ${entry.mood_score} · energy ${entry.energy_score}`}
                          </span>
                        </button>
                      </li>
                    ))}
                </ul>
              ) : (
                <div className="empty-state">Nothing recorded yet. Start with today.</div>
              )}
            </>
          )}
        </section>
      </div>
    </PageShell>
  );
}
