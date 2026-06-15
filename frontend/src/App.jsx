import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ContentGenerator from './pages/ContentGenerator';
import DocumentUpload from './pages/DocumentUpload';
import RagChat from './pages/RagChat';
import Settings from './pages/Settings';
import DocumentLibrary from './pages/DocumentLibrary';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generate" element={<ContentGenerator />} />
          <Route path="/upload" element={<DocumentUpload />} />
          <Route path="/library" element={<DocumentLibrary />} />
          <Route path="/rag-chat" element={<RagChat />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}