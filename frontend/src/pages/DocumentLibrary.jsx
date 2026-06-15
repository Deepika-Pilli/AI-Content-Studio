import { useState, useEffect } from 'react';
import { listUploads, listIndexes } from '../api/client';

export default function DocumentLibrary() {
  const [uploads, setUploads] = useState([]);
  const [indexes, setIndexes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [uploadRes, indexRes] = await Promise.all([
        listUploads(),
        listIndexes(),
      ]);
      setUploads(uploadRes.data.documents || []);
      setIndexes(indexRes.data.indexes || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const indexedIds = new Set(indexes.map((i) => i.document_id));

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Document Library</h1>
            <p className="page-subtitle">Uploaded documents and indexing status</p>
          </div>
          <button className="btn btn-secondary" onClick={fetchData} disabled={loading}>
            {loading ? 'Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="card">
        <h2>Uploaded Documents ({uploads.length})</h2>
        {uploads.length === 0 && !loading && (
          <p className="placeholder-text">No documents uploaded yet</p>
        )}
        {uploads.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Document ID</th>
                  <th>Size</th>
                  <th>Uploaded At</th>
                  <th>Indexed</th>
                </tr>
              </thead>
              <tbody>
                {uploads.map((doc) => {
                  const isIndexed = indexedIds.has(doc.id);
                  return (
                    <tr key={doc.id}>
                      <td className="cell-id" title={doc.id}>{doc.id}</td>
                      <td>{doc.file_size_display}</td>
                      <td>{new Date(doc.uploaded_at).toLocaleString()}</td>
                      <td>
                        <span className={`status-badge ${isIndexed ? 'indexed' : 'pending'}`}>
                          {isIndexed ? '✅ Indexed' : '⏳ Pending'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Indexed Documents ({indexes.length})</h2>
        {indexes.length === 0 && !loading && (
          <p className="placeholder-text">No documents indexed yet</p>
        )}
        {indexes.length > 0 && (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Document ID</th>
                  <th>Chunks</th>
                  <th>Vectors</th>
                </tr>
              </thead>
              <tbody>
                {indexes.map((idx) => (
                  <tr key={idx.document_id}>
                    <td className="cell-id" title={idx.document_id}>{idx.document_id}</td>
                    <td>{idx.total_chunks}</td>
                    <td>{idx.total_vectors}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}