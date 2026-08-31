/**
 * 404 Not Found page.
 */

import { Link } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';

export default function NotFound() {
  return (
    <div className="notfound-page">
      <Navbar />
      <div className="notfound-content">
        <h1>404</h1>
        <p>The page you're looking for doesn't exist.</p>
        <Link to="/" className="btn btn-primary">
          Go Home
        </Link>
      </div>
    </div>
  );
}
