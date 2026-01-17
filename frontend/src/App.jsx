import { useEffect, useState } from 'react';
import TranslationPanel from './components/TranslationPanel';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    // Check API health on mount
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health');
        if (response.ok) {
          const data = await response.json();
          setHealthStatus(data);
        }
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>Multi-Model Translation System</h1>
        <p>Translate from English or Traditional Chinese to Russian and Kazakh using multiple AI models</p>
      </header>

      <main className="container">
        <TranslationPanel />
      </main>

      <footer className="footer">
        <p>
          Powered by multiple AI models
          {healthStatus && (
            <span>
              {' '}&bull; {healthStatus.models_available.length} models available
              {healthStatus.ollama_connected && ' &bull; Ollama connected'}
            </span>
          )}
        </p>
      </footer>
    </div>
  );
}

export default App;
