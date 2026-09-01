/**
 * Journal — write entries, tag them, search them.
 *
 * Tags are the interesting half: `entry_tags` is a real many-to-many with a
 * composite (entry_id, tag_id) primary key, so an entry carries a *set* of
 * tags and a tag is reusable across entries. Updating an entry replaces its
 * whole tag set in one PUT rather than diffing rows here.
 *
 * Search hits the server, not the loaded page, so it covers every entry the
 * account owns and not just the twenty currently rendered.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { journalApi, tagApi } from '../api/wellness';
import PageShell from '../components/layout/PageShell';
import { formatTimestamp } from '../utils/dates';

const PAGE_SIZE = 10;
const SEARCH_DEBOUNCE_MS = 300;

const TAG_PALETTE = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b',
  '#10b981', '#06b6d4', '#84cc16', '#ef4444',
];

const EMPTY_DRAFT = { id: null, title: '', content: '', tag_ids: [] };

export default function Journal() {
  const [entries, setEntries] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const [tags, setTags] = useState([]);
  const [activeTagIds, setActiveTagIds] = useState([]);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [isComposing, setIsComposing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [confirmingId, setConfirmingId] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Debounced so typing does not fire a request per keystroke; the page
  // resets to 1 because page 3 of the old results means nothing here.
  useEffect(() => {
    const timer = setTimeout(() => {
      // oxlint-disable-next-line react/set-state-in-effect
      setSearch(searchInput.trim());
      setPage(1);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const loadEntries = useCallback(async () => {
    setError('');
    try {
      const params = { page, page_size: PAGE_SIZE };
      if (search) params.search = search;
      if (activeTagIds.length) params.tag_ids = activeTagIds;

      const result = await journalApi.list(params);
      setEntries(result.items || []);
      setTotalPages(result.totalPages || 1);
      setTotal(result.total || 0);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not load your journal.');
    } finally {
      setIsLoading(false);
    }
  }, [page, search, activeTagIds]);

  const loadTags = useCallback(async () => {
    try {
      setTags(await tagApi.list());
    } catch {
      // A failed tag list should not blank the entries; the filter row
      // simply renders empty and writing still works.
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    loadEntries();
  }, [loadEntries]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    loadTags();
  }, [loadTags]);

  const tagsById = useMemo(
    () => Object.fromEntries(tags.map((t) => [t.id, t])),
    [tags]
  );

  const openComposer = (entry = null) => {
    setDraft(
      entry
        ? {
            id: entry.id,
            title: entry.title,
            content: entry.content,
            tag_ids: entry.tags.map((t) => t.id),
          }
        : EMPTY_DRAFT
    );
    setIsComposing(true);
  };

  const toggleDraftTag = (id) =>
    setDraft((d) => ({
      ...d,
      tag_ids: d.tag_ids.includes(id)
        ? d.tag_ids.filter((t) => t !== id)
        : [...d.tag_ids, id],
    }));

  const handleSave = async (event) => {
    event.preventDefault();
    if (!draft.content.trim()) return;
    setIsSaving(true);
    setError('');
    try {
      const body = {
        title: draft.title.trim() || 'Untitled',
        content: draft.content.trim(),
        tag_ids: draft.tag_ids,
      };
      if (draft.id) await journalApi.update(draft.id, body);
      else await journalApi.create(body);

      setDraft(EMPTY_DRAFT);
      setIsComposing(false);
      if (!draft.id && page !== 1) setPage(1);
      else await loadEntries();
      await loadTags(); // entry counts on the chips have moved
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not save that entry.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id) => {
    setError('');
    try {
      await journalApi.remove(id);
      setConfirmingId(null);
      await loadEntries();
      await loadTags();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not delete that entry.');
    }
  };

  const handleCreateTag = async (name, color) => {
    const created = await tagApi.create({ name, color });
    await loadTags();
    return created;
  };

  const toggleFilter = (id) => {
    setActiveTagIds((current) =>
      current.includes(id) ? current.filter((t) => t !== id) : [...current, id]
    );
    setPage(1);
  };

  const isFiltered = Boolean(search) || activeTagIds.length > 0;

  return (
    <PageShell
      eyebrow="Reflection"
      title="Journal"
      subtitle={`${total} entr${total === 1 ? 'y' : 'ies'}${isFiltered ? ' matching' : ''}`}
      actions={
        <button type="button" className="btn btn-primary btn-sm" onClick={() => openComposer()}>
          New entry
        </button>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      {isComposing && (
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>{draft.id ? 'Edit entry' : 'New entry'}</h2>
              <p>Tags are shared across entries — reuse them so the analysis has something to group.</p>
            </div>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setIsComposing(false);
                setDraft(EMPTY_DRAFT);
              }}
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleSave}>
            <div className="form-group">
              <label htmlFor="entry-title">Title</label>
              <input
                id="entry-title"
                value={draft.title}
                maxLength={255}
                placeholder="Untitled"
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="entry-content">Entry</label>
              <textarea
                id="entry-content"
                value={draft.content}
                placeholder="What happened, and how it landed."
                onChange={(e) => setDraft({ ...draft, content: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Tags</label>
              <TagPicker
                tags={tags}
                selected={draft.tag_ids}
                onToggle={toggleDraftTag}
                onCreate={handleCreateTag}
                onCreated={(tag) => toggleDraftTag(tag.id)}
              />
            </div>

            <div className="form-row">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSaving || !draft.content.trim()}
              >
                {isSaving ? 'Saving…' : draft.id ? 'Save changes' : 'Publish entry'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="panel">
        <div className="panel-head">
          <div className="journal-search">
            <input
              type="search"
              value={searchInput}
              placeholder="Search titles and text…"
              aria-label="Search journal"
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
          {isFiltered && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setSearchInput('');
                setActiveTagIds([]);
                setPage(1);
              }}
            >
              Clear filters
            </button>
          )}
        </div>

        {tags.length > 0 && (
          <div className="chip-row">
            {tags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                className={`chip${activeTagIds.includes(tag.id) ? ' is-active' : ''}`}
                style={{ '--chip-color': tag.color }}
                onClick={() => toggleFilter(tag.id)}
              >
                <i />
                {tag.name}
                <span className="chip-count">{tag.entry_count ?? 0}</span>
              </button>
            ))}
          </div>
        )}

        {isLoading ? (
          <div className="page-loader">
            <span className="spinner" />
          </div>
        ) : entries.length ? (
          <ul className="entry-list">
            {entries.map((entry) => (
              <li className="entry-card" key={entry.id}>
                <div className="entry-head">
                  <h3>{entry.title}</h3>
                  <time>{formatTimestamp(entry.created_at)}</time>
                </div>

                <p className="entry-body">{entry.content}</p>

                <div className="entry-foot">
                  <div className="chip-row is-inline">
                    {entry.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="chip is-static"
                        style={{ '--chip-color': tagsById[tag.id]?.color || tag.color }}
                      >
                        <i />
                        {tag.name}
                      </span>
                    ))}
                  </div>

                  <div className="entry-tools">
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => openComposer(entry)}
                    >
                      Edit
                    </button>
                    {confirmingId === entry.id ? (
                      <>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(entry.id)}
                        >
                          Confirm
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => setConfirmingId(null)}
                        >
                          Keep
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => setConfirmingId(entry.id)}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty-state">
            {isFiltered
              ? 'Nothing matches those filters.'
              : 'Nothing written yet. The first entry is usually the hardest.'}
          </div>
        )}

        {totalPages > 1 && (
          <div className="pager">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        )}
      </section>
    </PageShell>
  );
}

/**
 * Tag selector with an inline "create" affordance.
 *
 * Names are normalised to lowercase server-side and `UNIQUE(user_id, name)`
 * rejects a duplicate, so the error is surfaced rather than swallowed —
 * otherwise a repeated name would silently do nothing.
 */
function TagPicker({ tags, selected, onToggle, onCreate, onCreated }) {
  const [isAdding, setIsAdding] = useState(false);
  const [name, setName] = useState('');
  const [color, setColor] = useState(TAG_PALETTE[0]);
  const [error, setError] = useState('');

  const submit = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setError('');
    try {
      const tag = await onCreate(trimmed, color);
      onCreated?.(tag);
      setName('');
      setIsAdding(false);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'That tag could not be created.');
    }
  };

  return (
    <div className="tag-picker">
      <div className="chip-row">
        {tags.map((tag) => (
          <button
            key={tag.id}
            type="button"
            className={`chip${selected.includes(tag.id) ? ' is-active' : ''}`}
            style={{ '--chip-color': tag.color }}
            onClick={() => onToggle(tag.id)}
          >
            <i />
            {tag.name}
          </button>
        ))}

        {!isAdding && (
          <button type="button" className="chip is-add" onClick={() => setIsAdding(true)}>
            + New tag
          </button>
        )}
      </div>

      {isAdding && (
        <div className="tag-create">
          <input
            value={name}
            maxLength={50}
            placeholder="tag name"
            aria-label="New tag name"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              // Enter would submit the surrounding entry form otherwise.
              if (e.key === 'Enter') {
                e.preventDefault();
                submit();
              }
            }}
          />
          <div className="swatch-row">
            {TAG_PALETTE.map((option) => (
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
          <button type="button" className="btn btn-primary btn-sm" onClick={submit}>
            Add
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setIsAdding(false);
              setError('');
            }}
          >
            Cancel
          </button>
        </div>
      )}

      {error && <p className="form-note is-bad">{error}</p>}
    </div>
  );
}
