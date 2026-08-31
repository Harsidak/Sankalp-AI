/**
 * Authentication API functions.
 */

import client from './client';
import { ENDPOINTS } from '../utils/constants';

export const authApi = {
  register: (data) =>
    client.post(ENDPOINTS.AUTH.REGISTER, data),

  login: (data) =>
    client.post(ENDPOINTS.AUTH.LOGIN, data),

  refreshToken: (refreshToken) =>
    client.post(ENDPOINTS.AUTH.REFRESH, { refresh_token: refreshToken }),

  googleAuth: (data) =>
    client.post(ENDPOINTS.AUTH.GOOGLE, data),

  getMe: () =>
    client.get(ENDPOINTS.AUTH.ME),

  logout: (refreshToken) =>
    client.post(ENDPOINTS.AUTH.LOGOUT, { refresh_token: refreshToken }),
};
