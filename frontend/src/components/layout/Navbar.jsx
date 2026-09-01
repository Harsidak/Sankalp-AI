/**
 * Site navigation — links flanking a centred wordmark.
 *
 * The frosted backdrop only appears once the page has scrolled, so the hero
 * reads as one uninterrupted canvas at rest.
 *
 * Signed in, the left cluster becomes the app's primary navigation; the
 * marketing anchors are hash links into the landing page and only make
 * sense signed out.
 */

import { useContext, useEffect, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { ThemeContext } from '../../context/ThemeContext';
import BrandMark from '../BrandMark';

const PUBLIC_LINKS = [
  { to: '/#practice', label: 'The Practice' },
  { to: '/#how', label: 'How It Works' },
];

const APP_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/checkin', label: 'Today' },
  { to: '/journal', label: 'Journal' },
  { to: '/habits', label: 'Habits' },
  { to: '/insights', label: 'Insights' },
];

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { isDark, toggleTheme } = useContext(ThemeContext);
  const navigate = useNavigate();
  const [isStuck, setIsStuck] = useState(false);

  useEffect(() => {
    const onScroll = () => setIsStuck(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav
      className={`site-nav${isStuck ? ' is-stuck' : ''}${isAuthenticated ? ' is-app' : ''}`}
    >
      <div className="nav-cluster is-left">
        {isAuthenticated
          ? APP_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) => `nav-link${isActive ? ' is-current' : ''}`}
              >
                {link.label}
              </NavLink>
            ))
          : PUBLIC_LINKS.map((link) => (
              <a key={link.to} href={link.to} className="nav-link">
                {link.label}
              </a>
            ))}
      </div>

      <Link to={isAuthenticated ? '/dashboard' : '/'} className="nav-brand">
        <BrandMark className="mark" />
        Sankalp<span style={{ color: 'var(--brand)' }}>AI</span>
      </Link>

      <div className="nav-cluster is-right">
        <button
          type="button"
          className="nav-theme"
          onClick={toggleTheme}
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="12" r="4.5" />
              <path
                d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M19.4 4.6l-2.1 2.1M6.7 17.3l-2.1 2.1"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 13.2A9 9 0 0 1 10.8 3a9 9 0 1 0 10.2 10.2z" />
            </svg>
          )}
        </button>

        {isAuthenticated ? (
          <>
            <NavLink
              to="/chat"
              className={({ isActive }) => `nav-link${isActive ? ' is-current' : ''}`}
            >
              Reflect
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) => `nav-link${isActive ? ' is-current' : ''}`}
            >
              {user?.full_name?.split(' ')[0] || user?.email}
            </NavLink>
            <button type="button" onClick={handleLogout} className="btn btn-outline btn-sm">
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">Sign in</Link>
            <Link to="/signup" className="btn btn-primary btn-sm">Start free</Link>
          </>
        )}
      </div>
    </nav>
  );
}
