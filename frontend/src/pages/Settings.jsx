export default function Settings() {
  return (
    <div className="page">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="page-subtitle">Application configuration</p>
      </div>

      <div className="settings-grid">
        <div className="card">
          <h2>Backend Configuration</h2>
          <div className="setting-item">
            <label>API URL</label>
            <code>http://127.0.0.1:8000</code>
          </div>
          <div className="setting-item">
            <label>Chunk Size</label>
            <code>1000 characters</code>
          </div>
          <div className="setting-item">
            <label>Chunk Overlap</label>
            <code>200 characters</code>
          </div>
          <div className="setting-item">
            <label>Embedding Model</label>
            <code>all-MiniLM-L6-v2 (384 dim)</code>
          </div>
          <div className="setting-item">
            <label>LLM Model</label>
            <code>llama-3.3-70b-versatile</code>
          </div>
        </div>

        <div className="card">
          <h2>Environment Variables</h2>
          <p className="setting-hint">
            Configure these in your <code>backend/.env</code> file:
          </p>
          <div className="env-list">
            <div className="env-item">
              <span className="env-key">GROQ_API_KEY</span>
              <span className="env-desc">Your Groq API key for LLM access</span>
            </div>
            <div className="env-item">
              <span className="env-key">CHUNK_SIZE</span>
              <span className="env-desc">Text chunk size (default: 1000)</span>
            </div>
            <div className="env-item">
              <span className="env-key">CHUNK_OVERLAP</span>
              <span className="env-desc">Chunk overlap (default: 200)</span>
            </div>
            <div className="env-item">
              <span className="env-key">EMBEDDING_MODEL</span>
              <span className="env-desc">HuggingFace model name</span>
            </div>
            <div className="env-item">
              <span className="env-key">MAX_FILE_SIZE_MB</span>
              <span className="env-desc">Max upload size (default: 10)</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Available Endpoints</h2>
          <div className="endpoint-list">
            {[
              { method: 'GET', path: '/', desc: 'Health check' },
              { method: 'GET', path: '/test-key', desc: 'API key status' },
              { method: 'POST', path: '/generate/', desc: 'Generate content' },
              { method: 'POST', path: '/upload/', desc: 'Upload document' },
              { method: 'POST', path: '/index/{id}', desc: 'Index document' },
              { method: 'POST', path: '/retrieve/', desc: 'Search chunks' },
              { method: 'POST', path: '/rag/query', desc: 'Ask questions' },
            ].map((ep, i) => (
              <div key={i} className="endpoint-item">
                <span className={`ep-method ${ep.method}`}>{ep.method}</span>
                <span className="ep-path">{ep.path}</span>
                <span className="ep-desc">{ep.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}