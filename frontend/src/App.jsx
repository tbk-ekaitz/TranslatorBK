import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import TranslationPanel from './components/TranslationPanel';
import DocumentPage from './components/DocumentPage';

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
    <Router>
      <div className="app">
        <header className="header">
          <h1>Multi-Model Translation System</h1>
          <p>Translate from English or Traditional Chinese to Russian and Kazakh using multiple AI models</p>

          <nav style={{
            marginTop: '15px',
            display: 'flex',
            gap: '20px',
            justifyContent: 'center'
          }}>
            <Link
              to="/"
              style={{
                color: 'white',
                textDecoration: 'none',
                padding: '8px 16px',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
                transition: 'background-color 0.3s'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'}
            >
              Text Translation
            </Link>
            <Link
              to="/document"
              style={{
                color: 'white',
                textDecoration: 'none',
                padding: '8px 16px',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
                transition: 'background-color 0.3s'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'}
            >
              Document Translation
            </Link>
          </nav>
        </header>

        <main className="container">
          <Routes>
            <Route path="/" element={<TranslationPanel />} />
            <Route path="/document" element={<DocumentPage />} />
          </Routes>
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
    </Router>
  );
}

export default App;
