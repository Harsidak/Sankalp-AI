/**
 * Dashboard page — authenticated user's home.
 *
 * Shows welcome panel, quick actions, and stats placeholders.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ragApi } from '../api/rag';
import Navbar from '../components/layout/Navbar';

export default function Dashboard() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await ragApi.listDocuments();
        setDocuments(response.data.data || []);
      } catch {
        // Documents may fail if user hasn't uploaded any
      } finally {
        setIsLoadingDocs(false);
      }
    };
    fetchDocuments();
  }, []);

  return (
    <div className="dashboard-page">
      <Navbar />

      <div className="dashboard-container">
        {/* Welcome Section */}
        <section className="dashboard-welcome">
          <h1>Welcome back, {user?.full_name || user?.email?.split('@')[0] || 'User'}!</h1>
          <p>Here's your SanKalp overview</p>
        </section>

        {/* Stats Cards */}
        <section className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-info">
              <h3>{documents.length}</h3>
              <p>Documents</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💬</div>
            <div className="stat-info">
              <h3>—</h3>
              <p>Chat Sessions</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🤖</div>
            <div className="stat-info">
              <h3>Active</h3>
              <p>AI Status</p>
            </div>
          </div>
        </section>

        {/* Quick Actions */}
        <section className="dashboard-actions">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <Link to="/chat" className="action-card">
              <span className="action-icon">💬</span>
              <h3>Start AI Chat</h3>
              <p>Chat with AI models</p>
            </Link>
            <label className="action-card" htmlFor="doc-upload">
              <span className="action-icon">📤</span>
              <h3>Upload Document</h3>
              <p>Add files for RAG</p>
              <input
                id="doc-upload"
                type="file"
                accept=".txt,.md,.pdf,.docx"
                style={{ display: 'none' }}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    try {
                      await ragApi.uploadDocument(file);
                      const response = await ragApi.listDocuments();
                      setDocuments(response.data.data || []);
                    } catch (err) {
                      alert(err.response?.data?.error?.message || 'Upload failed');
                    }
                  }
                }}
              />
            </label>
          </div>
        </section>

        {/* Documents List */}
        <section className="dashboard-documents">
          <h2>Your Documents</h2>
          {isLoadingDocs ? (
            <p>Loading documents...</p>
          ) : documents.length === 0 ? (
            <p className="empty-state">
              No documents yet. Upload a document to get started with RAG queries.
            </p>
          ) : (
            <div className="documents-list">
              {documents.map((doc) => (
                <div key={doc.id} className="document-item">
                  <div className="document-info">
                    <span className="document-name">{doc.filename}</span>
                    <span className="document-meta">
                      {doc.file_type.toUpperCase()} • {doc.chunk_count} chunks •{' '}
                      {doc.status}
                    </span>
                  </div>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={async () => {
                      if (confirm('Delete this document?')) {
                        try {
                          await ragApi.deleteDocument(doc.id);
                          setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
                        } catch {
                          alert('Failed to delete document');
                        }
                      }
                    }}
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
