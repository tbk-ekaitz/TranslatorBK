import { useState } from 'react';

const API_BASE_URL = '/api';

export default function TranslationPanel() {
  // Input states
  const [englishText, setEnglishText] = useState('');
  const [chineseText, setChineseText] = useState('');
  const [activeInput, setActiveInput] = useState(null); // 'en' or 'zh-TW'

  // Output states
  const [russianText, setRussianText] = useState('');
  const [kazakhText, setKazakhText] = useState('');

  // UI states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metadata, setMetadata] = useState(null);

  // Handle input focus/click - activate input and deactivate the other
  const handleInputFocus = (inputType) => {
    if (activeInput !== inputType) {
      setActiveInput(inputType);
      // Clear the other input
      if (inputType === 'en') {
        setChineseText('');
      } else {
        setEnglishText('');
      }
      // Clear outputs and error when switching
      setRussianText('');
      setKazakhText('');
      setError(null);
      setMetadata(null);
    }
  };

  // Handle double click to unlock a disabled input
  const handleDoubleClick = (inputType) => {
    // If this input is currently disabled (another is active), unlock it
    if (activeInput && activeInput !== inputType) {
      setActiveInput(inputType);
      // Clear the previously active input
      if (inputType === 'en') {
        setChineseText('');
      } else {
        setEnglishText('');
      }
      // Clear outputs and error
      setRussianText('');
      setKazakhText('');
      setError(null);
      setMetadata(null);
    }
  };

  // Handle text change
  const handleTextChange = (inputType, value) => {
    if (inputType === 'en') {
      setEnglishText(value);
      if (value && activeInput !== 'en') {
        handleInputFocus('en');
      }
    } else {
      setChineseText(value);
      if (value && activeInput !== 'zh-TW') {
        handleInputFocus('zh-TW');
      }
    }
  };

  // Handle translation
  const handleTranslate = async () => {
    // Validate inputs
    const sourceText = activeInput === 'en' ? englishText : chineseText;

    if (!sourceText || !sourceText.trim()) {
      setError('Please enter text to translate');
      return;
    }

    if (!activeInput) {
      setError('Please select a source language by clicking on an input field');
      return;
    }

    setIsLoading(true);
    setError(null);
    setRussianText('');
    setKazakhText('');
    setMetadata(null);

    try {
      const response = await fetch(`${API_BASE_URL}/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: sourceText,
          source_language: activeInput
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Translation failed');
      }

      const data = await response.json();

      // Set translations
      setRussianText(data.russian.best_translation);
      setKazakhText(data.kazakh.best_translation);

      // Set metadata
      setMetadata({
        processingTime: data.total_processing_time,
        russianConfidence: data.russian.evaluation_score,
        kazakhConfidence: data.kazakh.evaluation_score,
        russianModels: data.russian.all_translations.length,
        kazakhModels: data.kazakh.all_translations.length,
        evaluationMethod: data.russian.evaluation_method
      });

    } catch (err) {
      setError(err.message || 'An error occurred during translation');
      console.error('Translation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Check if translate button should be enabled
  const canTranslate = (activeInput === 'en' && englishText.trim()) ||
                       (activeInput === 'zh-TW' && chineseText.trim());

  return (
    <div className="translation-panel">
      {/* Source Language Input Section */}
      <div className="panel-section">
        <h2>Source Text</h2>
        <div className="input-group">
          {/* English Input */}
          <div className="input-container">
            <label htmlFor="english-input">
              English
              {activeInput === 'en' && <span className="status-badge success">Active</span>}
            </label>
            <textarea
              id="english-input"
              value={englishText}
              onChange={(e) => handleTextChange('en', e.target.value)}
              
              /* CAMBIO 1: Solo permitir focus/click si YA está activo. 
                Si no está activo, queremos forzar el doble clic. */
              onFocus={() => activeInput === 'en' && handleInputFocus('en')}
              onClick={() => activeInput === 'en' && handleInputFocus('en')}
              
              onDoubleClick={() => handleDoubleClick('en')}
              
              className={activeInput === 'zh-TW' ? 'disabled' : ''}
              
              /* CAMBIO 2: Usar readOnly en lugar de disabled */
              readOnly={activeInput === 'zh-TW'} 
              
              placeholder="Enter English text here... (Double-click to unlock if disabled)"
            />
          </div>

          {/* Traditional Chinese Input */}
          <div className="input-container">
            <label htmlFor="chinese-input">
              Traditional Chinese (繁體中文)
              {activeInput === 'zh-TW' && <span className="status-badge success">Active</span>}
            </label>
            <textarea
              id="chinese-input"
              value={chineseText}
              onChange={(e) => handleTextChange('zh-TW', e.target.value)}
              
              /* CAMBIO 1: Condicionar eventos de un solo clic */
              onFocus={() => activeInput === 'zh-TW' && handleInputFocus('zh-TW')}
              onClick={() => activeInput === 'zh-TW' && handleInputFocus('zh-TW')}
              
              onDoubleClick={() => handleDoubleClick('zh-TW')}
              
              className={activeInput === 'en' ? 'disabled' : ''}
              
              /* CAMBIO 2: Usar readOnly en lugar de disabled */
              readOnly={activeInput === 'en'}
              
              placeholder="在此輸入繁體中文... (雙擊解鎖若被禁用)"
            />
          </div>
        </div>
      </div>

      {/* Action Section */}
      <div className="action-section">
        <button
          className="translate-button"
          onClick={handleTranslate}
          disabled={!canTranslate || isLoading}
        >
          {isLoading ? 'Translating...' : 'Translate'}
        </button>
        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Processing with multiple models...</span>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Target Language Output Section */}
      <div className="panel-section">
        <h2>Translations</h2>
        <div className="output-group">
          {/* Russian Output */}
          <div className="output-container">
            <label htmlFor="russian-output">
              Russian (Русский)
              {metadata && (
                <span className="status-badge success">
                  {(metadata.russianConfidence * 100).toFixed(0)}% confidence
                </span>
              )}
            </label>
            <div
              id="russian-output"
              className={`output-box ${!russianText ? 'empty' : ''}`}
            >
              {russianText || 'Translation will appear here...'}
            </div>
          </div>

          {/* Kazakh Output */}
          <div className="output-container">
            <label htmlFor="kazakh-output">
              Kazakh (Қазақ)
              {metadata && (
                <span className="status-badge success">
                  {(metadata.kazakhConfidence * 100).toFixed(0)}% confidence
                </span>
              )}
            </label>
            <div
              id="kazakh-output"
              className={`output-box ${!kazakhText ? 'empty' : ''}`}
            >
              {kazakhText || 'Translation will appear here...'}
            </div>
          </div>
        </div>

        {/* Metadata Display */}
        {metadata && (
          <div className="metadata">
            <div className="metadata-item">
              <span>Processing Time:</span>
              <strong>{metadata.processingTime.toFixed(2)}s</strong>
            </div>
            <div className="metadata-item">
              <span>Models Used:</span>
              <strong>{metadata.russianModels} models</strong>
            </div>
            <div className="metadata-item">
              <span>Evaluation Method:</span>
              <strong>{metadata.evaluationMethod}</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
