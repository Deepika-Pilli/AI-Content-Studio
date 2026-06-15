import { useState } from 'react';
import { generateContent } from '../api/client';

const contentTypes = [
  { value: 'linkedin', label: 'LinkedIn Post' },
  { value: 'blog', label: 'Blog Article' },
  { value: 'twitter', label: 'Twitter/X Post' },
  { value: 'email', label: 'Email' },
  { value: 'general', label: 'General Content' },
];

const tones = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'humorous', label: 'Humorous' },
  { value: 'formal', label: 'Formal' },
];

export default function ContentGenerator() {
  const [prompt, setPrompt] = useState('');
  const [contentType, setContentType] = useState('general');
  const [tone, setTone] = useState('professional');
  const [maxTokens, setMaxTokens] = useState(512);
  const [temperature, setTemperature] = useState(0.7);
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    setOutput('');
    try {
      const res = await generateContent({ prompt, contentType, tone, maxTokens, temperature });
      setOutput(res.data.content);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Content Generator</h1>
        <p className="page-subtitle">Generate AI-powered content with custom tone and format</p>
      </div>

      <div className="content-grid">
        <div className="card">
          <form onSubmit={handleGenerate} className="generate-form">
            <div className="form-group">
              <label htmlFor="prompt">Prompt</label>
              <textarea
                id="prompt"
                rows={5}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Write a post about the benefits of AI in healthcare"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="contentType">Content Type</label>
                <select id="contentType" value={contentType} onChange={(e) => setContentType(e.target.value)}>
                  {contentTypes.map((ct) => (
                    <option key={ct.value} value={ct.value}>{ct.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="tone">Tone</label>
                <select id="tone" value={tone} onChange={(e) => setTone(e.target.value)}>
                  {tones.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="maxTokens">Max Tokens ({maxTokens})</label>
                <input
                  id="maxTokens"
                  type="range"
                  min={64}
                  max={2048}
                  step={64}
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                />
              </div>
              <div className="form-group">
                <label htmlFor="temperature">Temperature ({temperature.toFixed(1)})</label>
                <input
                  id="temperature"
                  type="range"
                  min={0}
                  max={2}
                  step={0.1}
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading || !prompt.trim()}>
              {loading ? 'Generating...' : 'Generate Content'}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Generated Output</h2>
          {error && <div className="error-box">{error}</div>}
          {loading && <p className="loading-text">Generating content with AI...</p>}
          {output && !loading && (
            <div className="output-box">
              <pre className="output-text">{output}</pre>
              <button className="btn btn-small" onClick={() => navigator.clipboard.writeText(output)}>
                Copy to Clipboard
              </button>
            </div>
          )}
          {!output && !loading && !error && (
            <p className="placeholder-text">Your generated content will appear here</p>
          )}
        </div>
      </div>
    </div>
  );
}