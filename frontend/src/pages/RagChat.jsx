import { useState } from 'react';
import { ragQuery } from '../api/client';

export default function RagChat() {
  const [documentId, setDocumentId] = useState('');
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!documentId.trim() || !question.trim()) return;

    setLoading(true);
    setError('');

    const userMsg = { role: 'user', content: question, docId: documentId };
    setHistory((prev) => [...prev, userMsg]);

    try {
      const res = await ragQuery(documentId, question, topK);
      const answer = res.data.answer || 'No answer generated';
      const chunks = res.data.retrieved_chunks || [];

      const botMsg = {
        role: 'assistant',
        content: answer,
        chunks,
        model: res.data.model,
      };
      setHistory((prev) => [...prev, botMsg]);
    } catch (err) {
      setError(err.message);
      setHistory((prev) => [...prev, { role: 'error', content: err.message }]);
    } finally {
      setLoading(false);
      setQuestion('');
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>RAG Chat</h1>
        <p className="page-subtitle">Ask questions about your indexed documents</p>
      </div>

      <div className="chat-layout">
        <div className="chat-sidebar card">
          <h3>Document ID</h3>
          <div className="form-group">
            <input
              type="text"
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
              placeholder="upload_abc123_doc.txt"
            />
          </div>
          <div className="form-group">
            <label>Context Chunks ({topK})</label>
            <input
              type="range"
              min={1}
              max={10}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
            />
          </div>
          {error && <div className="error-box">{error}</div>}
        </div>

        <div className="chat-main card">
          <div className="chat-messages">
            {history.length === 0 && (
              <div className="chat-welcome">
                <span className="chat-welcome-icon">💬</span>
                <p>Ask a question about an indexed document to get started</p>
                <ol className="chat-steps">
                  <li>Upload a document via Document Upload page</li>
                  <li>Index the document</li>
                  <li>Enter the Document ID here and ask a question</li>
                </ol>
              </div>
            )}
            {history.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : msg.role === 'error' ? '⚠️' : '🤖'}
                </div>
                <div className="message-body">
                  <div className="message-content">{msg.content}</div>
                  {msg.chunks && msg.chunks.length > 0 && (
                    <details className="chunks-details">
                      <summary>Sources ({msg.chunks.length} chunks)</summary>
                      {msg.chunks.map((chunk, j) => (
                        <div key={j} className="chunk-item">
                          <div className="chunk-meta">
                            Score: {chunk.score.toFixed(4)} | Chunk {chunk.chunk_index}
                          </div>
                          <p className="chunk-text">{chunk.text.slice(0, 200)}...</p>
                        </div>
                      ))}
                    </details>
                  )}
                  {msg.model && (
                    <div className="message-model">Model: {msg.model}</div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-body">
                  <div className="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="chat-input-form">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your document..."
              disabled={loading || !documentId.trim()}
              className="chat-input"
            />
            <button
              type="submit"
              className="btn btn-primary btn-send"
              disabled={loading || !question.trim() || !documentId.trim()}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}