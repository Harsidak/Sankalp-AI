/**
 * Landing page — public-facing hero section with feature highlights and CTAs.
 */

import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Navbar from '../components/layout/Navbar';

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="landing-page">
      <Navbar />

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>SanKalp</h1>
          <p className="hero-subtitle">
            AI-Powered Platform for Intelligent Document Analysis & Insights
          </p>
          <p className="hero-description">
            Upload your documents, ask questions, and get intelligent answers powered by
            cutting-edge AI. Built with RAG technology for accurate, context-aware responses.
          </p>
          <div className="hero-actions">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary btn-lg">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link to="/signup" className="btn btn-primary btn-lg">
                  Get Started Free
                </Link>
                <Link to="/login" className="btn btn-outline btn-lg">
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2>Why SanKalp?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔐</div>
            <h3>Secure Authentication</h3>
            <p>
              Enterprise-grade security with JWT tokens, Google OAuth,
              and encrypted password storage.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI-Powered Chat</h3>
            <p>
              Chat with multiple AI models including GPT-4o and Gemini.
              Real-time streaming responses.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📄</div>
            <h3>RAG Pipeline</h3>
            <p>
              Upload documents and query them with AI. Get contextual answers
              with source citations.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Lightning Fast</h3>
            <p>
              Built on FastAPI and React for blazing performance.
              Async everything, zero blocking.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔌</div>
            <h3>Pluggable Architecture</h3>
            <p>
              Swap AI providers, databases, and features without
              touching core code. Built for extensibility.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🚀</div>
            <h3>Production Ready</h3>
            <p>
              Rate limiting, error handling, structured logging,
              and Docker support out of the box.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; 2026 SanKalp. Built for the hackathon.</p>
      </footer>
    </div>
  );
}
