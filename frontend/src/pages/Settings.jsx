/**
 * Settings — profile, password, and the two account-level operations.
 *
 * The data section is worth its space: the export reports a row count per
 * table, and deleting the account reports the counts the cascade actually
 * removed. Those are the same numbers, which is the visible proof that
 * `ON DELETE CASCADE` from users is doing the work rather than a pile of
 * service-side deletes that could stop half way.
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usersApi } from '../api/users';
import { useAuth } from '../hooks/useAuth';
import PageShell from '../components/layout/PageShell';

/** Ordered for reading, and labelled the way a person would say it. */
const COUNT_LABELS = {
  checkins: 'Check-ins',
  journal_entries: 'Journal entries',
  entry_tags: 'Entry–tag links',
  tags: 'Tags',
  habits: 'Habits',
  habit_logs: 'Habit logs',
  chat_sessions: 'Chat sessions',
  refresh_tokens: 'Active sessions',
};

export default function Settings() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [counts, setCounts] = useState(null);
  const [error, setError] = useState('');

  const loadCounts = useCallback(async () => {
    try {
      const exported = await usersApi.exportAccount();
      setCounts(exported.counts);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not read your account data.');
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    loadCounts();
  }, [loadCounts]);

  const isPasswordAccount = user?.auth_provider === 'local';

  return (
    <PageShell
      eyebrow="Account"
      title="Settings"
      subtitle={user?.email}
    >
      {error && <div className="alert alert-error">{error}</div>}

      <ProfileSection user={user} onSaved={refreshUser} />

      {isPasswordAccount && <PasswordSection />}

      <DataSection counts={counts} />

      <DangerSection
        needsPassword={isPasswordAccount}
        onDeleted={async () => {
          await logout();
          navigate('/', { replace: true });
        }}
      />
    </PageShell>
  );
}

function ProfileSection({ user, onSaved }) {
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setIsSaving(true);
    setStatus('');
    setError('');
    try {
      await usersApi.updateProfile({ full_name: fullName.trim() || null });
      await onSaved();
      setStatus('Saved.');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not save your profile.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Profile</h2>
          <p>Your email is your login and cannot be changed here.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={submit} className="settings-form">
        <div className="form-group">
          <label htmlFor="full-name">Name</label>
          <input
            id="full-name"
            value={fullName}
            maxLength={255}
            placeholder="How you want to be greeted"
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>

        <div className="form-row">
          <button type="submit" className="btn btn-primary" disabled={isSaving}>
            {isSaving ? 'Saving…' : 'Save profile'}
          </button>
          {status && <span className="form-note is-good">{status}</span>}
        </div>
      </form>
    </section>
  );
}

function PasswordSection() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setStatus('');
    setError('');

    if (next !== confirm) {
      setError('The two new passwords do not match.');
      return;
    }
    if (next.length < 8) {
      setError('Use at least 8 characters.');
      return;
    }

    setIsSaving(true);
    try {
      await usersApi.changePassword({ current_password: current, new_password: next });
      setCurrent('');
      setNext('');
      setConfirm('');
      setStatus('Password changed.');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not change your password.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Password</h2>
          <p>Changing it does not sign out your other sessions.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={submit} className="settings-form">
        <div className="form-group">
          <label htmlFor="current-password">Current password</label>
          <input
            id="current-password"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="new-password">New password</label>
          <input
            id="new-password"
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirm-password">Repeat new password</label>
          <input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </div>

        <div className="form-row">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSaving || !current || !next}
          >
            {isSaving ? 'Changing…' : 'Change password'}
          </button>
          {status && <span className="form-note is-good">{status}</span>}
        </div>
      </form>
    </section>
  );
}

function DataSection({ counts }) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState('');

  /**
   * Builds the file in the browser from the JSON already returned, rather
   * than pointing a link at the endpoint: the endpoint needs an
   * Authorization header, which a plain navigation cannot send.
   */
  const download = async () => {
    setIsExporting(true);
    setError('');
    try {
      const exported = await usersApi.exportAccount();
      const blob = new Blob([JSON.stringify(exported, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sankalp-export-${exported.exported_at.slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not build your export.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Your data</h2>
          <p>Everything this account owns, table by table.</p>
        </div>
        <button
          type="button"
          className="btn btn-outline btn-sm"
          onClick={download}
          disabled={isExporting}
        >
          {isExporting ? 'Preparing…' : 'Download JSON'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {counts ? (
        <ul className="count-grid">
          {Object.entries(COUNT_LABELS).map(([key, label]) => (
            <li key={key}>
              <strong>{counts[key] ?? 0}</strong>
              <span>{label}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="page-loader">
          <span className="spinner" />
        </div>
      )}
    </section>
  );
}

function DangerSection({ needsPassword, onDeleted }) {
  const [isOpen, setIsOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setIsDeleting(true);
    setError('');
    try {
      await usersApi.deleteAccount({
        confirm,
        password: needsPassword ? password : undefined,
      });
      await onDeleted();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not delete the account.');
      setIsDeleting(false);
    }
  };

  return (
    <section className="panel is-danger">
      <div className="panel-head">
        <div>
          <h2>Delete account</h2>
          <p>
            Permanent. The user row goes, and the database removes every check-in,
            entry, tag, habit and log with it. There is no export afterwards —
            download yours first.
          </p>
        </div>
        {!isOpen && (
          <button type="button" className="btn btn-danger btn-sm" onClick={() => setIsOpen(true)}>
            Delete…
          </button>
        )}
      </div>

      {isOpen && (
        <form onSubmit={submit} className="settings-form">
          {error && <div className="alert alert-error">{error}</div>}

          {needsPassword && (
            <div className="form-group">
              <label htmlFor="delete-password">Current password</label>
              <input
                id="delete-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="delete-confirm">
              Type <code>DELETE</code> to confirm
            </label>
            <input
              id="delete-confirm"
              value={confirm}
              placeholder="DELETE"
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>

          <div className="form-row">
            <button
              type="submit"
              className="btn btn-danger"
              disabled={isDeleting || confirm !== 'DELETE' || (needsPassword && !password)}
            >
              {isDeleting ? 'Deleting…' : 'Delete my account permanently'}
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setIsOpen(false);
                setError('');
                setConfirm('');
                setPassword('');
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
