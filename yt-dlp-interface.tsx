import React, { useState } from 'react';
import { Download, Video, Music, Loader2, CheckCircle, AlertCircle, Search, Activity } from 'lucide-react';

export default function YtDlpInterface() {
  const [url, setUrl] = useState('');
  const [type, setType] = useState('video');
  const [selectedQuality, setSelectedQuality] = useState('');
  const [availableQualities, setAvailableQualities] = useState([]);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [loadingQualities, setLoadingQualities] = useState(false);
  const [audioAnalysis, setAudioAnalysis] = useState(null);
  const [analyzingAudio, setAnalyzingAudio] = useState(false);

  const BACKEND_URL = 'https://YOUR-USERNAME-yt-dlp-backend.hf.space';

  const fetchQualities = async () => {
    if (!url.trim()) {
      setStatus('error');
      setMessage('Please enter a valid URL');
      return;
    }

    setLoadingQualities(true);
    setAvailableQualities([]);
    setSelectedQuality('');
    setStatus('idle');
    setMessage('');
    setAudioAnalysis(null);

    try {
      const response = await fetch(`${BACKEND_URL}/formats`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          type: type
        })
      });

      const data = await response.json();

      if (response.ok) {
        setAvailableQualities(data.formats);
        if (data.formats.length > 0) {
          setSelectedQuality(data.formats[0].format_id);
        }
        setMessage('Available qualities loaded');
      } else {
        setStatus('error');
        setMessage(data.error || 'Error fetching qualities');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Connection error. Check if backend is active.');
    } finally {
      setLoadingQualities(false);
    }
  };

  const analyzeAudio = async () => {
    if (!selectedQuality) {
      setStatus('error');
      setMessage('Please select a quality first');
      return;
    }

    setAnalyzingAudio(true);
    setAudioAnalysis(null);

    try {
      const response = await fetch(`${BACKEND_URL}/analyze-audio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          format_id: selectedQuality
        })
      });

      const data = await response.json();

      if (response.ok) {
        setAudioAnalysis(data.analysis);
      } else {
        setStatus('error');
        setMessage(data.error || 'Error analyzing audio');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Connection error during analysis.');
    } finally {
      setAnalyzingAudio(false);
    }
  };

  const handleDownload = async () => {
    if (!url.trim()) {
      setStatus('error');
      setMessage('Please enter a valid URL');
      return;
    }

    if (!selectedQuality) {
      setStatus('error');
      setMessage('Please select a quality');
      return;
    }

    setStatus('loading');
    setMessage('Processing download...');
    setDownloadUrl('');

    try {
      const response = await fetch(`${BACKEND_URL}/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          format_id: selectedQuality,
          type: type
        })
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(data.message || 'Download ready!');
        setDownloadUrl(data.download_url);
      } else {
        setStatus('error');
        setMessage(data.error || 'Error processing download');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Connection error. Check if backend is active.');
    }
  };

  const getQualityColor = (quality) => {
    if (quality === 'excellent') return 'text-green-400';
    if (quality === 'good') return 'text-blue-400';
    if (quality === 'fair') return 'text-yellow-400';
    return 'text-red-400';
  };

  const getQualityBg = (quality) => {
    if (quality === 'excellent') return 'bg-green-500/20 border-green-500/50';
    if (quality === 'good') return 'bg-blue-500/20 border-blue-500/50';
    if (quality === 'fair') return 'bg-yellow-500/20 border-yellow-500/50';
    return 'bg-red-500/20 border-red-500/50';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full mb-4">
            <Download className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">ytDownloader</h1>
        </div>

        <div className="space-y-6">
          {/* URL Input */}
          <div>
            <label className="block text-white font-medium mb-2">Video URL</label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={status === 'loading' || loadingQualities}
            />
          </div>

          {/* Type Selection */}
          <div>
            <label className="block text-white font-medium mb-2">Download Type</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => {
                  setType('video');
                  setAvailableQualities([]);
                  setSelectedQuality('');
                  setAudioAnalysis(null);
                }}
                disabled={status === 'loading' || loadingQualities}
                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all ${
                  type === 'video'
                    ? 'bg-purple-500 text-white shadow-lg'
                    : 'bg-white/10 text-white hover:bg-white/20'
                } ${status === 'loading' || loadingQualities ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <Video className="w-5 h-5" />
                <span>Video</span>
              </button>
              <button
                onClick={() => {
                  setType('audio');
                  setAvailableQualities([]);
                  setSelectedQuality('');
                  setAudioAnalysis(null);
                }}
                disabled={status === 'loading' || loadingQualities}
                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all ${
                  type === 'audio'
                    ? 'bg-purple-500 text-white shadow-lg'
                    : 'bg-white/10 text-white hover:bg-white/20'
                } ${status === 'loading' || loadingQualities ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <Music className="w-5 h-5" />
                <span>Audio (MP3)</span>
              </button>
            </div>
          </div>

          {/* Get Qualities Button */}
          <button
            onClick={fetchQualities}
            disabled={status === 'loading' || loadingQualities}
            className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-cyan-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loadingQualities ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching qualities...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search Available Qualities
              </>
            )}
          </button>

          {/* Quality Dropdown */}
          {availableQualities.length > 0 && (
            <div>
              <label className="block text-white font-medium mb-2">Available Quality</label>
              <select
                value={selectedQuality}
                onChange={(e) => {
                  setSelectedQuality(e.target.value);
                  setAudioAnalysis(null);
                }}
                disabled={status === 'loading'}
                className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {availableQualities.map((quality) => (
                  <option key={quality.format_id} value={quality.format_id} className="bg-gray-900">
                    {quality.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Audio Analyzer Button (only for MP3) */}
          {type === 'audio' && availableQualities.length > 0 && (
            <button
              onClick={analyzeAudio}
              disabled={analyzingAudio}
              className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {analyzingAudio ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing audio quality...
                </>
              ) : (
                <>
                  <Activity className="w-5 h-5" />
                  Analyze Audio Quality
                </>
              )}
            </button>
          )}

          {/* Audio Analysis Results */}
          {audioAnalysis && (
            <div className={`p-4 rounded-lg border ${getQualityBg(audioAnalysis.quality)}`}>
              <div className="flex items-start gap-3">
                <Activity className={`w-6 h-6 ${getQualityColor(audioAnalysis.quality)} flex-shrink-0 mt-0.5`} />
                <div className="flex-1">
                  <h3 className={`font-semibold ${getQualityColor(audioAnalysis.quality)} mb-2`}>
                    Audio Quality: {audioAnalysis.quality.toUpperCase()}
                  </h3>
                  <div className="text-white text-sm space-y-1">
                    <p><strong>Bitrate:</strong> {audioAnalysis.bitrate}</p>
                    <p><strong>Sample Rate:</strong> {audioAnalysis.sample_rate}</p>
                    <p><strong>Codec:</strong> {audioAnalysis.codec}</p>
                    {audioAnalysis.distortion && (
                      <p className="text-yellow-300 mt-2">⚠️ {audioAnalysis.distortion}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Download Button */}
          {availableQualities.length > 0 && (
            <button
              onClick={handleDownload}
              disabled={status === 'loading'}
              className="w-full py-4 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {status === 'loading' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="w-5 h-5" />
                  Download
                </>
              )}
            </button>
          )}

          {/* Status Messages */}
          {status !== 'idle' && (
            <div
              className={`p-4 rounded-lg flex items-start gap-3 ${
                status === 'success'
                  ? 'bg-green-500/20 border border-green-500/50'
                  : status === 'error'
                  ? 'bg-red-500/20 border border-red-500/50'
                  : 'bg-blue-500/20 border border-blue-500/50'
              }`}
            >
              {status === 'success' ? (
                <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" />
              ) : status === 'error' ? (
                <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
              ) : (
                <Loader2 className="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5 animate-spin" />
              )}
              <div className="flex-1">
                <p className="text-white">{message}</p>
                {downloadUrl && (
                  <a
                    href={downloadUrl}
                    download
                    className="inline-block mt-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-all"
                  >
                    Download File
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}