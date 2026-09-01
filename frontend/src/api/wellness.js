/**
 * Wellness domain API: check-ins, journal, habits, tags, dashboard.
 *
 * Every backend response is wrapped in { success, data, ... }; these helpers
 * unwrap to `data` so callers never reach through two layers of envelope.
 */

import client from './client';
import { ENDPOINTS } from '../utils/constants';

const unwrap = (res) => res.data.data;

/** PaginatedResponse keeps its counters as siblings of `data`, not nested. */
const unwrapPage = (res) => {
  const { data, total, page, page_size: pageSize, total_pages: totalPages } = res.data;
  return { items: data, total, page, pageSize, totalPages };
};

export const checkinApi = {
  /** Not paginated: the range is bounded by `days` (or start/end) instead. */
  list: (params) => client.get(ENDPOINTS.CHECKINS.ROOT, { params }).then(unwrap),
  today: () => client.get(ENDPOINTS.CHECKINS.TODAY).then(unwrap),
  streak: () => client.get(ENDPOINTS.CHECKINS.STREAK).then(unwrap),
  create: (body) => client.post(ENDPOINTS.CHECKINS.ROOT, body).then(unwrap),
  update: (id, body) => client.patch(ENDPOINTS.CHECKINS.ONE(id), body).then(unwrap),
  remove: (id) => client.delete(ENDPOINTS.CHECKINS.ONE(id)),
};

export const journalApi = {
  /**
   * `indexes: null` matters: axios serialises arrays as `tag_ids[]=a&tag_ids[]=b`
   * by default, and FastAPI reads a repeated `tag_ids=a&tag_ids=b` instead, so
   * bracketed keys arrive as no filter at all rather than as an error.
   */
  list: (params) =>
    client
      .get(ENDPOINTS.JOURNAL.ROOT, { params, paramsSerializer: { indexes: null } })
      .then(unwrapPage),
  get: (id) => client.get(ENDPOINTS.JOURNAL.ONE(id)).then(unwrap),
  create: (body) => client.post(ENDPOINTS.JOURNAL.ROOT, body).then(unwrap),
  update: (id, body) => client.put(ENDPOINTS.JOURNAL.ONE(id), body).then(unwrap),
  remove: (id) => client.delete(ENDPOINTS.JOURNAL.ONE(id)),
};

export const habitApi = {
  list: (params) => client.get(ENDPOINTS.HABITS.ROOT, { params }).then(unwrap),
  get: (id) => client.get(ENDPOINTS.HABITS.ONE(id)).then(unwrap),
  create: (body) => client.post(ENDPOINTS.HABITS.ROOT, body).then(unwrap),
  update: (id, body) => client.patch(ENDPOINTS.HABITS.ONE(id), body).then(unwrap),
  remove: (id) => client.delete(ENDPOINTS.HABITS.ONE(id)),
  /** Completion is row presence: this toggles the log for a date. */
  toggle: (id, body = {}) => client.post(ENDPOINTS.HABITS.LOG(id), body).then(unwrap),
};

export const tagApi = {
  list: () => client.get(ENDPOINTS.TAGS.ROOT).then(unwrap),
  create: (body) => client.post(ENDPOINTS.TAGS.ROOT, body).then(unwrap),
  update: (id, body) => client.patch(ENDPOINTS.TAGS.ONE(id), body).then(unwrap),
  remove: (id) => client.delete(ENDPOINTS.TAGS.ONE(id)),
};

export const dashboardApi = {
  summary: (days = 30) =>
    client.get(ENDPOINTS.DASHBOARD.SUMMARY, { params: { days } }).then(unwrap),
};

export const insightsApi = {
  summary: (days = 30) =>
    client.get(ENDPOINTS.INSIGHTS.SUMMARY, { params: { days } }).then(unwrap),
};
