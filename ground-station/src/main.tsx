import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/global.css';

// No StrictMode: services hold live streams/timers that must not double-start.
createRoot(document.getElementById('root')!).render(<App />);
