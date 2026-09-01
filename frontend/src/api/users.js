/**
 * Account API: profile, password, whole-account export and deletion.
 *
 * Unwrapped to `data` like the wellness helpers, so pages never reach
 * through both the axios response and the APIResponse envelope.
 */

import client from './client';
import { ENDPOINTS } from '../utils/constants';

const unwrap = (res) => res.data.data;

export const usersApi = {
  getProfile: () => client.get(ENDPOINTS.USERS.PROFILE).then(unwrap),

  updateProfile: (body) => client.put(ENDPOINTS.USERS.PROFILE, body).then(unwrap),

  /** Returns the envelope itself: this endpoint carries a message, no data. */
  changePassword: (body) => client.put(ENDPOINTS.USERS.PASSWORD, body).then((res) => res.data),

  /** The full account as one JSON document, for the "download my data" button. */
  exportAccount: () => client.get(ENDPOINTS.USERS.EXPORT).then(unwrap),

  /**
   * Permanent. `body` must carry confirm: 'DELETE' and, for password
   * accounts, the current password. A DELETE with a body needs the payload
   * under `data` in the config -- axios has no second body argument here.
   */
  deleteAccount: (body) =>
    client.delete(ENDPOINTS.USERS.ACCOUNT, { data: body }).then(unwrap),
};
