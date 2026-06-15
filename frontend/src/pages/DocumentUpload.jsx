import { useState } from 'react';
import { uploadDocument, indexDocument } from '../api/client';

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [step, setStep] = useState('upload'); // upload | indexed

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) {
      const ext = f.name.split('.').pop().toLowerCase();
      if (!['pdf', 'docx', 'txt'].includes(ext)) {
        setError('Only PDF, DOCX, and TXT files are supported');
        setFile(null);
        return;
      }
      if (f.size > 10 * 1024 * 1024) {
        setError('File size must be under 10 MB');
        setFile(null);
        return;
      }
      setFile(f);
      setError('');
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const res = await uploadDocument(file);
      setResult(res.data);
      setStep('upload');
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleIndex = async () => {
    if (!result?.document?.id) return;
    setIndexing(true);
    setError('');
    try {
      const res = await indexDocument(result.document.id);
      setResult((prev) => ({ ...prev, indexResult: res.data }));
      setStep('indexed');
    } catch (err) {
      setError(err.message);
    } finally {
      setIndexing(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setResult(null);
    setError('');
    setStep('upload');
    document.getElementById('file-input').value = '';
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Document Upload</h1>
        <p className="page-subtitle">Upload, index, and search documents</p>
      </div>

      <div className="steps-indicator">
        <div className={`step ${file ? 'active' : ''}`}>1. Select File</div>
        <div className={`step ${result?.document?.id ? 'active' : ''}`}>2. Upload</div>
        <div className={`step ${step === 'indexed' ? 'active' : ''}`}>3. Index</div>
      </div>

      <div className="card upload-card">
        <div className="form-group">
          <label htmlFor="file-input">Choose a file (PDF, DOCX, or TXT)</label>
          <input
            id="file-input"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            className="file-input"
          />
          {file && (
            <div className="file-info">
              <span>📄 {file.name}</span>
              <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}
        </div>

        {error && <div className="error-box">{error}</div>}

        {file && !result && (
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>
        )}

        {result?.document && step === 'upload' && !result.indexResult && (
          <div className="result-section">
            <h3>Upload Successful ✅</h3>
            <div className="result-grid">
              <div><strong>ID:</strong> {result.document.id}</div>
              <div><strong>Size:</strong> {result.document.file_size_display}</div>
              <div><strong>Type:</strong> {result.document.extension}</div>
              <div><strong>Chars:</strong> {result.document.text_length}</div>
            </div>
            <div className="preview-box">
              <strong>Preview:</strong>
              <p>{result.document.text_preview}</p>
            </div>
            <button className="btn btn-primary" onClick={handleIndex} disabled={indexing}>
              {indexing ? 'Indexing...' : 'Index Document'}
            </button>
          </div>
        )}

        {result?.indexResult && (
          <div className="result-section">
            <h3>Indexing Complete ✅</h3>
            <div className="result-grid">
              <div><strong>Chunks:</strong> {result.indexResult.total_chunks}</div>
              <div><strong>Vectors:</strong> {result.indexResult.total_vectors}</div>
              <div><strong>Dimension:</strong> {result.indexResult.embedding_dimension}</div>
              <div><strong>Model:</strong> {result.indexResult.embedding_model}</div>
            </div>
            <button className="btn btn-secondary" onClick={resetForm}>
              Upload Another Document
            </button>
          </div>
        )}
      </div>
    </div>
  );
}