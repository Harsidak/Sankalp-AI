/**
 * Site navigation — links flanking a centred wordmark.
 *
 * The frosted backdrop only appears once the page has scrolled, so the hero
 * reads as one uninterrupted canvas at rest.
 */

import { useContext, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { ThemeContext } from '../../context/ThemeContext';
import BrandMark from '../BrandMark';

const PUBLIC_LINKS = [
  { to: '/#practice', label: 'The Practice' },
  { to: '/#how', label: 'How It Works' },
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
    <nav className={`site-nav${isStuck ? ' is-stuck' : ''}`}>
      <div className="nav-cluster is-left">
        {isAuthenticated ? (
          <>
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/chat" className="nav-link">Reflect</Link>
          </>
        ) : (
          PUBLIC_LINKS.map((link) => (
            <a key={link.to} href={link.to} className="nav-link">
              {link.label}
            </a>
          ))
        )}
      </div>

      <Link to="/" className="nav-brand">
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
            <span className="nav-link" style={{ cursor: 'default' }}>
              {user?.full_name?.split(' ')[0] || user?.email}
            </span>
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
