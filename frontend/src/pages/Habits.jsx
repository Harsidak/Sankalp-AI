/**
 * Habits — create them, and mark them done across a rolling two weeks.
 *
 * Completion is row presence, not a boolean column: `UNIQUE(habit_id,
 * completed_date)` in habit_logs means a day is either logged or it is not,
 * so the toggle endpoint inserts or deletes one row and returns the
 * recomputed streaks. This page trusts that response rather than
 * re-fetching the list, which keeps a grid of ~70 cells responsive.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { habitApi } from '../api/wellness';
import PageShell from '../components/layout/PageShell';
import { formatDay, lastNDays, todayISO } from '../utils/dates';

const GRID_DAYS = 14;

const PALETTE = [
  '#8b5cf6', '#6366f1', '#06b6d4', '#10b981',
  '#84cc16', '#f59e0b', '#ec4899', '#ef4444',
];

const WEEKDAY_INITIALS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

const EMPTY_DRAFT = { name: '', color: PALETTE[0], target_per_week: 7 };

export default function Habits() {
  const [habits, setHabits] = useState([]);
  const [showArchived, setShowArchived] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [busyCell, setBusyCell] = useState(null);

  const days = useMemo(() => lastNDays(GRID_DAYS), []);
  const today = todayISO();

  const load = useCallback(async () => {
    setError('');
    try {
      setHabits(await habitApi.list({ include_archived: showArchived }));
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not load your habits.');
    } finally {
      setIsLoading(false);
    }
  }, [showArchived]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    load();
  }, [load]);

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!draft.name.trim()) return;
    setIsCreating(true);
    setError('');
    try {
      await habitApi.create({ ...draft, name: draft.name.trim() });
      setDraft(EMPTY_DRAFT);
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not create that habit.');
    } finally {
      setIsCreating(false);
    }
  };

  /**
   * Applies the toggle result in place. `completed` tells us which way it
   * went, so the local `completed_dates` set can be corrected without
   * guessing, and the streaks come back already recomputed by the service.
   */
  const handleToggle = async (habit, iso) => {
    setBusyCell(`${habit.id}:${iso}`);
    setError('');
    try {
      const result = await habitApi.toggle(habit.id, { completed_date: iso });
      setHabits((current) =>
        current.map((h) => {
          if (h.id !== habit.id) return h;
          const dates = new Set(h.completed_dates);
          if (result.completed) dates.add(iso);
          else dates.delete(iso);
          return {
            ...h,
            completed_dates: [...dates].sort(),
            current_streak: result.current_streak,
            longest_streak: result.longest_streak,
            completed_today: iso === today ? result.completed : h.completed_today,
          };
        })
      );
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not update that day.');
    } finally {
      setBusyCell(null);
    }
  };

  const handleUpdate = async (habit, changes) => {
    setError('');
    try {
      await habitApi.update(habit.id, changes);
      setEditingId(null);
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not update that habit.');
    }
  };

  const handleDelete = async (habit) => {
    setError('');
    try {
      await habitApi.remove(habit.id);
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not delete that habit.');
    }
  };

  return (
    <PageShell
      eyebrow="Practice"
      title="Habits"
      subtitle="Small things, kept often. The grid is the last two weeks."
      actions={
        <label className="toggle-inline">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show archived
        </label>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Add a habit</h2>
            <p>Give it a colour so it is recognisable everywhere else.</p>
          </div>
        </div>

        <form onSubmit={handleCreate} className="habit-form">
          <div className="form-group">
            <label htmlFor="habit-name">Name</label>
            <input
              id="habit-name"
              value={draft.name}
              maxLength={100}
              placeholder="Walk 20 minutes"
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label htmlFor="habit-target">Days per week</label>
            <select
              id="habit-target"
              value={draft.target_per_week}
              onChange={(e) => setDraft({ ...draft, target_per_week: Number(e.target.value) })}
            >
              {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Colour</label>
            <div className="swatch-row">
              {PALETTE.map((color) => (
                <button
                  key={color}
                  type="button"
                  className={`swatch${draft.color === color ? ' is-active' : ''}`}
                  style={{ background: color }}
                  aria-label={`Use colour ${color}`}
                  onClick={() => setDraft({ ...draft, color })}
                />
              ))}
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={isCreating || !draft.name.trim()}>
            {isCreating ? 'Adding…' : 'Add habit'}
          </button>
        </form>
      </section>

      {isLoading ? (
        <div className="page-loader">
          <span className="spinner" />
        </div>
      ) : habits.length ? (
        <div className="habit-list">
          {habits.map((habit) => {
            const done = new Set(habit.completed_dates);
            const kept = days.filter((d) => done.has(d)).length;
            const target = Math.max(Math.round((habit.target_per_week * GRID_DAYS) / 7), 1);

            return (
              <section
                className={`panel habit-card${habit.is_archived ? ' is-archived' : ''}`}
                key={habit.id}
                style={{ '--habit-color': habit.color }}
              >
                <div className="panel-head">
                  <div className="habit-title">
                    <span className="habit-dot" />
                    <div>
                      <h2>{habit.name}</h2>
                      <p>
                        {habit.current_streak} day streak · longest {habit.longest_streak} ·{' '}
                        {kept}/{target} this fortnight
                        {habit.is_archived && ' · archived'}
                      </p>
                    </div>
                  </div>

                  <div className="habit-tools">
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => setEditingId(editingId === habit.id ? null : habit.id)}
                    >
                      {editingId === habit.id ? 'Close' : 'Edit'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleUpdate(habit, { is_archived: !habit.is_archived })}
                    >
                      {habit.is_archived ? 'Restore' : 'Archive'}
                    </button>
                  </div>
                </div>

                <div className="habit-grid">
                  {days.map((iso) => {
                    const isDone = done.has(iso);
                    const weekday = WEEKDAY_INITIALS[new Date(`${iso}T00:00:00`).getDay()];
                    return (
                      <button
                        key={iso}
                        type="button"
                        className={`habit-cell${isDone ? ' is-done' : ''}${iso === today ? ' is-today' : ''}`}
                        disabled={busyCell === `${habit.id}:${iso}`}
                        title={`${formatDay(iso)} — ${isDone ? 'done' : 'not done'}`}
                        aria-pressed={isDone}
                        aria-label={`${habit.name} on ${formatDay(iso)}`}
                        onClick={() => handleToggle(habit, iso)}
                      >
                        <span className="cell-day">{weekday}</span>
                        <span className="cell-date">{iso.slice(8)}</span>
                      </button>
                    );
                  })}
                </div>

                {editingId === habit.id && (
                  <HabitEditor
                    habit={habit}
                    onSave={(changes) => handleUpdate(habit, changes)}
                    onDelete={() => handleDelete(habit)}
                  />
                )}
              </section>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          No habits yet. Add one above — the streaks start counting from the first day you mark.
        </div>
      )}
    </PageShell>
  );
}

/**
 * Inline editor. Deletion is separated behind a second click, because it
 * takes every habit_log row with it via ON DELETE CASCADE.
 */
function HabitEditor({ habit, onSave, onDelete }) {
  const [name, setName] = useState(habit.name);
  const [color, setColor] = useState(habit.color);
  const [target, setTarget] = useState(habit.target_per_week);
  const [confirming, setConfirming] = useState(false);

  return (
    <div className="habit-editor">
      <div className="form-group">
        <label htmlFor={`name-${habit.id}`}>Name</label>
        <input
          id={`name-${habit.id}`}
          value={name}
          maxLength={100}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label htmlFor={`target-${habit.id}`}>Days per week</label>
        <select
          id={`target-${habit.id}`}
          value={target}
          onChange={(e) => setTarget(Number(e.target.value))}
        >
          {[1, 2, 3, 4, 5, 6, 7].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Colour</label>
        <div className="swatch-row">
          {PALETTE.map((option) => (
            <button
              key={option}
              type="button"
              className={`swatch${color === option ? ' is-active' : ''}`}
              style={{ background: option }}
              aria-label={`Use colour ${option}`}
              onClick={() => setColor(option)}
            />
          ))}
        </div>
      </div>

      <div className="form-row">
        <button
          type="button"
          className="btn btn-primary btn-sm"
          disabled={!name.trim()}
          onClick={() => onSave({ name: name.trim(), color, target_per_week: target })}
        >
          Save changes
        </button>

        {confirming ? (
          <>
            <span className="form-note">Delete this habit and its whole history?</span>
            <button type="button" className="btn btn-danger btn-sm" onClick={onDelete}>
              Yes, delete
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setConfirming(false)}
            >
              Cancel
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setConfirming(true)}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
