/**
 * Application route configuration.
 *
 * Every authenticated surface is wrapped once here rather than checking
 * auth inside each page, so a new page cannot accidentally ship unguarded.
 */

import { Routes, Route } from 'react-router-dom';
import Landing from '../pages/Landing';
import Login from '../pages/Login';
import Signup from '../pages/Signup';
import Dashboard from '../pages/Dashboard';
import CheckIn from '../pages/CheckIn';
import Journal from '../pages/Journal';
import Habits from '../pages/Habits';
import Insights from '../pages/Insights';
import Settings from '../pages/Settings';
import Chat from '../pages/Chat';
import NotFound from '../pages/NotFound';
import ProtectedRoute from './ProtectedRoute';

const PROTECTED = [
  ['/dashboard', Dashboard],
  ['/checkin', CheckIn],
  ['/journal', Journal],
  ['/habits', Habits],
  ['/insights', Insights],
  ['/settings', Settings],
  ['/chat', Chat],
];

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Protected routes */}
      {PROTECTED.map(([path, Page]) => (
        <Route
          key={path}
          path={path}
          element={
            <ProtectedRoute>
              <Page />
            </ProtectedRoute>
          }
        />
      ))}

      {/* 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
