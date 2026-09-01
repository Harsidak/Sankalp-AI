/**
 * Dashboard — the aggregated view of the trailing window.
 *
 * One request to /dashboard/summary supplies everything on the page, so the
 * cards can never disagree about which range they are describing.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { dashboardApi, checkinApi } from '../api/wellness';
import Navbar from '../components/layout/Navbar';
import MoodTrend from '../components/charts/MoodTrend';
import StreakRing from '../components/charts/StreakRing';

const RANGES = [7, 30, 90];

export default function Dashboard() {
  const { user } = useAuth();
  const [days, setDays] = useState(30);
  const [summary, setSummary] = useState(null);
  const [streak, setStreak] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const [summaryData, streakData] = await Promise.all([
        dashboardApi.summary(days),
        checkinApi.streak(),
      ]);
      setSummary(summaryData);
      setStreak(streakData);
    } catch (err) {
      setError(
        err.response?.data?.error?.message || 'Could not load your dashboard.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    // Fetching on range change is exactly the "synchronise with an external
    // system" case the rule exempts; the loading flag it objects to is what
    // keeps the old window's chart from being read as the new one's.
    // oxlint-disable-next-line react/set-state-in-effect
    load();
  }, [load]);

  /**
   * Consistency is the share of days in the window that were checked in.
   * Derived here rather than on the server: it is presentation, not truth.
   */
  const consistency = useMemo(() => {
    if (!summary?.range_days) return 0;
    return Math.round((summary.checkin_count / summary.range_days) * 100);
  }, [summary]);

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }, []);

  const firstName = user?.full_name?.split(' ')[0] || 'there';

  return (
    <div className="dashboard-page">
      <Navbar />

      <main className="dashboard-container">
        <header className="dashboard-welcome">
          <p className="eyebrow">Your Practice</p>
          <h1>
            {greeting}, {firstName}.
          </h1>
          <p>
            {streak?.current_streak
              ? `${streak.current_streak} day${streak.current_streak === 1 ? '' : 's'} in a row. Keep the thread going.`
              : 'No streak running. One check-in starts a new one.'}
          </p>
        </header>

        {error && <div className="alert alert-error">{error}</div>}

        {isLoading && !summary ? (
          <div className="page-loader">
            <span className="spinner" />
          </div>
        ) : (
          summary && (
            <>
              <section className="dashboard-stats">
                <article className="stat-card">
                  <span className="stat-icon">◎</span>
                  <div className="stat-info">
                    <h3>{summary.average_mood?.toFixed(1) ?? '—'}</h3>
                    <p>Average mood</p>
                  </div>
                </article>
                <article className="stat-card">
                  <span className="stat-icon">◇</span>
                  <div className="stat-info">
                    <h3>{summary.average_energy?.toFixed(1) ?? '—'}</h3>
                    <p>Average energy</p>
                  </div>
                </article>
                <article className="stat-card">
                  <span className="stat-icon">✦</span>
                  <div className="stat-info">
                    <h3>{streak?.longest_streak ?? 0}</h3>
                    <p>Longest streak</p>
                  </div>
                </article>
                <article className="stat-card">
                  <span className="stat-icon">✎</span>
                  <div className="stat-info">
                    <h3>{summary.journal_count}</h3>
                    <p>Journal entries</p>
                  </div>
                </article>
              </section>

              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h2>How the last {summary.range_days} days felt</h2>
                    <p>
                      {summary.checkin_count} check-in
                      {summary.checkin_count === 1 ? '' : 's'} · {consistency}% of days
                    </p>
                  </div>
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
                </div>
                <MoodTrend points={summary.mood_trend} />
              </section>

              <div className="panel-row">
                <section className="panel">
                  <div className="panel-head">
                    <h2>Habits this window</h2>
                    <Link to="/habits" className="btn btn-ghost btn-sm">
                      Manage
                    </Link>
                  </div>

                  {summary.habit_completions.length ? (
                    <div className="ring-row">
                      {summary.habit_completions.map((habit) => (
                        <div className="ring-item" key={habit.habit_id}>
                          <StreakRing
                            value={habit.completions}
                            target={Math.max(
                              Math.round((habit.target * summary.range_days) / 7),
                              1
                            )}
                            color={habit.color}
                            label="done"
                          />
                          <p className="ring-name">{habit.name}</p>
                          <p className="ring-meta">{habit.current_streak} day streak</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      No habits yet. <Link to="/habits">Add your first</Link>.
                    </div>
                  )}
                </section>

                <section className="panel">
                  <div className="panel-head">
                    <h2>What you wrote about</h2>
                    <Link to="/journal" className="btn btn-ghost btn-sm">
                      Journal
                    </Link>
                  </div>

                  {summary.top_tags.length ? (
                    <ul className="tag-bars">
                      {summary.top_tags.map((tag) => {
                        const max = summary.top_tags[0].count || 1;
                        return (
                          <li key={tag.name}>
                            <span className="tag-name">
                              <i style={{ background: tag.color }} />
                              {tag.name}
                            </span>
                            <span className="tag-bar">
                              <i
                                style={{
                                  width: `${(tag.count / max) * 100}%`,
                                  background: tag.color,
                                }}
                              />
                            </span>
                            <span className="tag-count">{tag.count}</span>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <div className="empty-state">
                      No tagged entries yet. <Link to="/journal">Write one</Link>.
                    </div>
                  )}
                </section>
              </div>

              <section className="dashboard-actions">
                <h2>Quick actions</h2>
                <div className="actions-grid">
                  <Link to="/checkin" className="action-card">
                    <span className="action-icon">◎</span>
                    <h3>Check in</h3>
                    <p>Log today&rsquo;s mood, energy and sleep.</p>
                  </Link>
                  <Link to="/journal" className="action-card">
                    <span className="action-icon">✎</span>
                    <h3>Write an entry</h3>
                    <p>Get it out of your head and tag it.</p>
                  </Link>
                  <Link to="/habits" className="action-card">
                    <span className="action-icon">✦</span>
                    <h3>Mark habits</h3>
                    <p>Keep the streaks honest.</p>
                  </Link>
                  <Link to="/insights" className="action-card">
                    <span className="action-icon">◈</span>
                    <h3>See the patterns</h3>
                    <p>What actually moves your mood, measured.</p>
                  </Link>
                  <Link to="/chat" className="action-card">
                    <span className="action-icon">✧</span>
                    <h3>Ask for a reflection</h3>
                    <p>Let the AI read your patterns back to you.</p>
                  </Link>
                </div>
              </section>
            </>
          )
        )}
      </main>
    </div>
  );
}
