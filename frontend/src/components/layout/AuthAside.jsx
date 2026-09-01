/**
 * The brand panel beside the login and signup forms. Hidden below 900px,
 * where the form gets the whole screen.
 */

import { Link } from 'react-router-dom';
import BrandMark from '../BrandMark';

export default function AuthAside({ line, sub }) {
  return (
    <aside className="auth-aside">
      <Link to="/" className="nav-brand">
        <BrandMark className="mark" />
        SankalpAI
      </Link>

      <div>
        <p className="auth-aside-word">
          {line}
          <em>{sub}</em>
        </p>
        <p>
          Check in daily, write it down, keep the small promises. SankalpAI holds the
          record so you can see the shape of your own weeks.
        </p>
      </div>

      <p className="auth-quote">
        &ldquo;Sankalp&rdquo; — a resolve made quietly, and kept.
      </p>
    </aside>
  );
}
