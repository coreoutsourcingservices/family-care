import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './styles.css';
import './responsive.css';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element is missing');
createRoot(rootElement).render(<BrowserRouter><App /></BrowserRouter>);
