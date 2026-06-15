import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/generate', label: 'Content Generator', icon: '✍️' },
  { to: '/upload', label: 'Document Upload', icon: '📄' },
  { to: '/library', label: 'Document Library', icon: '📚' },
  { to: '/rag-chat', label: 'RAG Chat', icon: '💬' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-logo">✦</span>
        <span className="sidebar-title">AI Studio</span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'active' : ''}`
            }
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className="sidebar-version">v1.0.0</span>
      </div>
    </aside>
  );
}