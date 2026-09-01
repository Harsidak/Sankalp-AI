/**
 * Insights — correlations rather than counts.
 *
 * Nothing on this page is stored. Every number arrives from one request to
 * /insights/summary, where four SQL aggregations compute it: mood split by
 * whether a habit was kept that day (a conditional AVG over an outer join
 * whose NULL side *means* "missed"), mood by weekday, the distribution of
 * scores, and mood on the days a tag was written about.
 *
 * The headline stays silent when the evidence is thin, which is deliberate:
 * a wellness app that invents correlations from four data points is worse
 * than one that says nothing.
 */

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { insightsApi } from '../api/wellness';
import PageShell from '../components/layout/PageShell';

const RANGES = [30, 90, 180];

/** Mood lives on 1-5, so the usable bar range is 4 points wide, not 5. */
const moodToPercent = (mood) =>
  mood == null ? 0 : Math.max(((mood - 1) / 4) * 100, 2);

const format = (value) => (value == null ? '—' : value.toFixed(1));

export default function Insights() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      setData(await insightsApi.summary(days));
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not compute your insights.');
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    load();
  }, [load]);

  const ranked = [...(data?.habit_impact || [])].sort(
    (a, b) => (b.delta ?? -Infinity) - (a.delta ?? -Infinity)
  );
  const maxBucket = Math.max(1, ...(data?.mood_distribution || []).map((b) => b.count));

  return (
    <PageShell
      eyebrow="Analysis"
      title="What your data says"
      subtitle="Computed in SQL over the window, every time you open this page."
      actions={
        <div className="range-switch">
          {RANGES.map((range) => (
            <button
              key={range}
              type="button"
              className={range === days ? 'is-active' : ''}
              onClick={() => setDays(range)}
            >
              {range}d
            </button>
          ))}
        </div>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      {isLoading && !data ? (
        <div className="page-loader">
          <span className="spinner" />
        </div>
      ) : (
        data && (
          <>
            {data.headline ? (
              <section className="headline-card">
                <p className="eyebrow">Strongest signal</p>
                <p className="headline-text">{data.headline}</p>
              </section>
            ) : (
              <section className="headline-card is-quiet">
                <p className="eyebrow">Not enough yet</p>
                <p className="headline-text">
                  There is no signal worth reporting over this window. Keep checking in —
                  a habit needs a handful of days on both sides before the difference
                  means anything.
                </p>
              </section>
            )}

            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Mood, with and without each habit</h2>
                  <p>
                    Average mood on the days you kept it, against the days you did not.
                    Only days you checked in are counted.
                  </p>
                </div>
              </div>

              {ranked.length ? (
                <ul className="impact-list">
                  {ranked.map((habit) => (
                    <li key={habit.habit_id} style={{ '--habit-color': habit.color }}>
                      <div className="impact-head">
                        <span className="impact-name">
                          <i />
                          {habit.name}
                        </span>
                        {habit.delta == null ? (
                          <span className="delta is-none">not enough days</span>
                        ) : (
                          <span className={`delta${habit.delta >= 0 ? ' is-up' : ' is-down'}`}>
                            {habit.delta >= 0 ? '+' : ''}
                            {habit.delta.toFixed(1)}
                          </span>
                        )}
                      </div>

                      <div className="impact-bars">
                        <div className="impact-bar">
                          <span className="impact-label">Kept ({habit.days_done}d)</span>
                          <span className="impact-track">
                            <i
                              className="is-done"
                              style={{ width: `${moodToPercent(habit.mood_when_done)}%` }}
                            />
                          </span>
                          <span className="impact-value">{format(habit.mood_when_done)}</span>
                        </div>

                        <div className="impact-bar">
                          <span className="impact-label">Missed ({habit.days_missed}d)</span>
                          <span className="impact-track">
                            <i
                              className="is-missed"
                              style={{ width: `${moodToPercent(habit.mood_when_missed)}%` }}
                            />
                          </span>
                          <span className="impact-value">{format(habit.mood_when_missed)}</span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="empty-state">
                  No habits tracked in this window. <Link to="/habits">Add one</Link>.
                </div>
              )}
            </section>

            <div className="panel-row">
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h2>By day of the week</h2>
                    <p>
                      {data.best_weekday
                        ? `${data.best_weekday} reads highest${data.hardest_weekday ? `, ${data.hardest_weekday} lowest` : ''}.`
                        : 'Not enough check-ins to compare days yet.'}
                    </p>
                  </div>
                </div>

                <div className="weekday-chart">
                  {data.weekday.map((day) => (
                    <div className="weekday-col" key={day.weekday}>
                      <span className="weekday-value">{format(day.avg_mood)}</span>
                      <span className="weekday-track">
                        <i
                          className={
                            day.label === data.best_weekday
                              ? 'is-best'
                              : day.label === data.hardest_weekday
                                ? 'is-worst'
                                : ''
                          }
                          style={{ height: `${moodToPercent(day.avg_mood)}%` }}
                        />
                      </span>
                      <span className="weekday-name">{day.label.slice(0, 3)}</span>
                      <span className="weekday-count">{day.checkins}</span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h2>How the days spread out</h2>
                    <p>Every check-in in the window, by the score you gave it.</p>
                  </div>
                </div>

                <ul className="distribution">
                  {data.mood_distribution.map((bucket) => (
                    <li key={bucket.score}>
                      <span className="dist-score" style={{ background: `var(--mood-${bucket.score})` }}>
                        {bucket.score}
                      </span>
                      <span className="dist-track">
                        <i
                          style={{
                            width: `${(bucket.count / maxBucket) * 100}%`,
                            background: `var(--mood-${bucket.score})`,
                          }}
                        />
                      </span>
                      <span className="dist-count">{bucket.count}</span>
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Mood on the days you wrote about…</h2>
                  <p>
                    Journal tags joined to that day&rsquo;s check-in. A tag with no
                    check-in on its day contributes an entry but no mood.
                  </p>
                </div>
                <Link to="/journal" className="btn btn-ghost btn-sm">
                  Journal
                </Link>
              </div>

              {data.tag_mood.length ? (
                <ul className="tag-bars">
                  {data.tag_mood.map((tag) => (
                    <li key={tag.name}>
                      <span className="tag-name">
                        <i style={{ background: tag.color }} />
                        {tag.name}
                      </span>
                      <span className="tag-bar">
                        <i
                          style={{
                            width: `${moodToPercent(tag.avg_mood)}%`,
                            background: tag.color,
                          }}
                        />
                      </span>
                      <span className="tag-count">
                        {format(tag.avg_mood)}
                        <em>{tag.entries} entr{tag.entries === 1 ? 'y' : 'ies'}</em>
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="empty-state">
                  No tagged entries in this window. <Link to="/journal">Write one</Link>.
                </div>
              )}
            </section>
          </>
        )
      )}
    </PageShell>
  );
}
