import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main>
      <span className="brand">FamilyCare+</span>
      <h1>Doctor portal</h1>
      <p>React + TypeScript setup is ready. Portal pages will be added here.</p>
    </main>
  );
}

const root = document.getElementById('root');
if (!root) throw new Error('Root element is missing');
createRoot(root).render(<App />);