/**
 * User management API functions.
 */

import client from './client';
import { ENDPOINTS } from '../utils/constants';

export const usersApi = {
  getProfile: () =>
    client.get(ENDPOINTS.USERS.PROFILE),

  updateProfile: (data) =>
    client.put(ENDPOINTS.USERS.PROFILE, data),

  changePassword: (data) =>
    client.put(ENDPOINTS.USERS.PASSWORD, data),
};
