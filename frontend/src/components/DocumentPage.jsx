import { useState, useEffect } from 'react';

const DocumentPage = () => {
  // Upload section state
  const [selectedFile, setSelectedFile] = useState(null);
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Status section state
  const [jobId, setJobId] = useState('');
  const [jobStatus, setJobStatus] = useState(null);
  const [pollingActive, setPollingActive] = useState(false);

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const extension = file.name.split('.').pop().toLowerCase();
      const allowedExtensions = ['pdf', 'txt', 'md', 'docx'];
      const maxSizeMB = 100;
      const maxSizeBytes = maxSizeMB * 1024 * 1024;

      if (!allowedExtensions.includes(extension)) {
        setUploadError(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`);
        setSelectedFile(null);
      } else if (file.size > maxSizeBytes) {
        setUploadError(`File is too large. Maximum size is ${maxSizeMB}MB (file is ${(file.size / 1024 / 1024).toFixed(2)}MB)`);
        setSelectedFile(null);
      } else {
        setSelectedFile(file);
        setUploadError(null);
      }
    }
  };

  // Upload document
  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Please select a file');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('source_language', sourceLanguage);

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 413) {
          throw new Error('File is too large. Maximum size is 100MB');
        }
        try {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        } catch (e) {
          throw new Error('Upload failed');
        }
      }

      const data = await response.json();

      // Auto-fill job ID and start polling
      setJobId(data.job_id);
      setPollingActive(true);

      // Reset upload form
      setSelectedFile(null);
      setSourceLanguage('en');

    } catch (error) {
      setUploadError(error.message);
    } finally {
      setUploading(false);
    }
  };

  // Fetch job status
  const fetchJobStatus = async (id) => {
    try {
      const response = await fetch(`/api/documents/jobs/${id}/status`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Job not found');
        }
        throw new Error('Failed to fetch job status');
      }

      const data = await response.json();
      setJobStatus(data);

      // Stop polling if job is completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        setPollingActive(false);
      }

    } catch (error) {
      setJobStatus({ error: error.message });
      setPollingActive(false);
    }
  };

  // Handle job ID input
  const handleCheckStatus = () => {
    if (jobId.trim()) {
      setPollingActive(true);
    }
  };

  // Polling effect
  useEffect(() => {
    if (!pollingActive || !jobId) {
      return;
    }

    // Fetch immediately
    fetchJobStatus(jobId);

    // Then poll every 500ms
    const interval = setInterval(() => {
      fetchJobStatus(jobId);
    }, 500);

    return () => clearInterval(interval);
  }, [pollingActive, jobId]);

  // Download document
  const handleDownload = async (language) => {
    try {
      const response = await fetch(`/api/documents/jobs/${jobId}/download/${language}`);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `document_${language}`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      alert(`Download failed: ${error.message}`);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Document Translation</h1>

      {/* Upload Section */}
      <div style={{
        border: '2px solid #ddd',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '30px',
        backgroundColor: '#f9f9f9'
      }}>
        <h2>Upload Document</h2>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Select Document (PDF, TXT, MD, DOCX - Max 100MB):
          </label>
          <input
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={handleFileChange}
            style={{ display: 'block', marginBottom: '10px' }}
          />
          {selectedFile && (
            <p style={{ color: '#666', fontSize: '14px' }}>
              Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)}MB)
            </p>
          )}
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Source Language:
          </label>
          <select
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
            style={{
              padding: '8px',
              fontSize: '14px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          >
            <option value="en">English</option>
            <option value="zh-TW">Traditional Chinese</option>
          </select>
        </div>

        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: uploading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: uploading ? 'not-allowed' : 'pointer',
          }}
        >
          {uploading ? 'Uploading...' : 'Translate Document'}
        </button>

        {uploadError && (
          <p style={{ color: 'red', marginTop: '10px' }}>
            Error: {uploadError}
          </p>
        )}
      </div>

      {/* Status Check Section */}
      <div style={{
        border: '2px solid #ddd',
        borderRadius: '8px',
        padding: '20px',
        backgroundColor: '#f9f9f9'
      }}>
        <h2>Check Translation Status</h2>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Job ID:
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="Enter job ID or upload a document"
              style={{
                flex: 1,
                padding: '8px',
                fontSize: '14px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}
            />
            <button
              onClick={handleCheckStatus}
              disabled={!jobId.trim()}
              style={{
                padding: '8px 20px',
                fontSize: '14px',
                backgroundColor: !jobId.trim() ? '#ccc' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: !jobId.trim() ? 'not-allowed' : 'pointer',
              }}
            >
              Check Status
            </button>
          </div>
        </div>

        {/* Status Display */}
        {jobStatus && !jobStatus.error && (
          <div style={{
            marginTop: '20px',
            padding: '15px',
            backgroundColor: 'white',
            borderRadius: '4px',
            border: '1px solid #ddd'
          }}>
            <h3 style={{ marginTop: 0 }}>Status Information</h3>

            <p><strong>Document:</strong> {jobStatus.document_name}</p>
            <p><strong>Source Language:</strong> {jobStatus.source_language === 'en' ? 'English' : 'Traditional Chinese'}</p>
            <p><strong>Status:</strong> <span style={{
              color: jobStatus.status === 'completed' ? 'green' :
                     jobStatus.status === 'failed' ? 'red' :
                     jobStatus.status === 'processing' ? 'orange' : 'gray',
              fontWeight: 'bold',
              textTransform: 'capitalize'
            }}>{jobStatus.status}</span></p>

            {jobStatus.status === 'processing' && (
              <>
                <p><strong>Progress:</strong> {jobStatus.progress.toFixed(1)}%</p>
                <div style={{
                  width: '100%',
                  backgroundColor: '#e0e0e0',
                  borderRadius: '4px',
                  height: '20px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${jobStatus.progress}%`,
                    backgroundColor: '#007bff',
                    height: '100%',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  Translated {jobStatus.translated_phrases} of {jobStatus.total_phrases} phrases
                </p>
              </>
            )}

            {jobStatus.status === 'completed' && (
              <div style={{ marginTop: '20px' }}>
                <h4>Download Translations:</h4>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => handleDownload('russian')}
                    style={{
                      padding: '10px 15px',
                      backgroundColor: '#17a2b8',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Download Russian
                  </button>
                  <button
                    onClick={() => handleDownload('kazakh')}
                    style={{
                      padding: '10px 15px',
                      backgroundColor: '#17a2b8',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Download Kazakh
                  </button>
                  <button
                    onClick={() => handleDownload('json')}
                    style={{
                      padding: '10px 15px',
                      backgroundColor: '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Download JSON
                  </button>
                  <button
                    onClick={() => handleDownload('original')}
                    style={{
                      padding: '10px 15px',
                      backgroundColor: '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Download Original (MD)
                  </button>
                </div>
              </div>
            )}

            {jobStatus.status === 'failed' && (
              <p style={{ color: 'red', marginTop: '10px' }}>
                <strong>Error:</strong> {jobStatus.error_message}
              </p>
            )}
          </div>
        )}

        {jobStatus && jobStatus.error && (
          <p style={{ color: 'red', marginTop: '10px' }}>
            Error: {jobStatus.error}
          </p>
        )}
      </div>
    </div>
  );
};

export default DocumentPage;
