import { useState, useEffect } from 'react';
import { healthCheck } from '../api/client';

export default function Dashboard() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    healthCheck()
      .then((res) => {
        setStatus(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">Welcome to AI Content Studio</p>
      </div>

      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-icon">✍️</div>
          <div className="stat-info">
            <h3>Content Generation</h3>
            <p>Generate AI-powered content for LinkedIn, blogs, tweets & more</p>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon">📄</div>
          <div className="stat-info">
            <h3>Document Upload</h3>
            <p>Upload PDF, DOCX, TXT files for processing</p>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon">💬</div>
          <div className="stat-info">
            <h3>RAG Queries</h3>
            <p>Ask questions about your documents with AI</p>
          </div>
        </div>
      </div>

      <div className="card status-card">
        <h2>Backend Status</h2>
        {loading && <p className="loading-text">Connecting to backend...</p>}
        {error && (
          <div className="error-box">
            <span className="status-dot offline" />
            <span>Backend unavailable: {error}</span>
          </div>
        )}
        {status && (
          <div className="status-info">
            <div className="status-row">
              <span className="status-dot online" />
              <span>Backend is running</span>
            </div>
            <div className="status-row">
              <span>Groq API:</span>
              <span className={status.groq_configured ? 'text-green' : 'text-yellow'}>
                {status.groq_configured ? 'Configured' : 'Not configured'}
              </span>
            </div>
            <div className="status-row">
              <span>Model:</span>
              <span>llama-3.3-70b-versatile</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}