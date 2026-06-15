/**
 * API Client for AI Content Studio Backend.
 * Handles all HTTP communication with the FastAPI backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for LLM generation
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
  },
});

// ─── Response interceptor for error handling ─────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail?.error ||
      error.response?.data?.detail?.detail ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

// ─── Health ──────────────────────────────────────────────────────

export const healthCheck = () => api.get('/');

// ─── Content Generation ──────────────────────────────────────────

export const generateContent = (data) =>
  api.post('/generate/', {
    prompt: data.prompt,
    content_type: data.contentType || 'general',
    tone: data.tone || 'professional',
    max_tokens: data.maxTokens || 512,
    temperature: data.temperature || 0.7,
  });

// ─── Document Upload ─────────────────────────────────────────────

export const listUploads = () => api.get('/upload/');

export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });
};

// ─── Document Indexing ───────────────────────────────────────────

export const listIndexes = () => api.get('/index/');

export const indexDocument = (documentId) =>
  api.post(`/index/${documentId}`);

// ─── Retrieval ───────────────────────────────────────────────────

export const retrieveChunks = (documentId, query, topK = 5) =>
  api.post('/retrieve/', {
    document_id: documentId,
    query,
    top_k: topK,
  });

// ─── RAG Query ───────────────────────────────────────────────────

export const ragQuery = (documentId, question, topK = 5) =>
  api.post('/rag/query', {
    document_id: documentId,
    question,
    top_k: topK,
  });

export default api;