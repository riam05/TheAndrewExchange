import React, { useState, useEffect, useRef } from 'react';

interface AnalysisResult {
  success: boolean;
  script?: string;
  script_path?: string;
  debate_data?: any;
  data?: any;
  saved_to: string;
  error?: string;
}

interface AudioFile {
  filename: string;
  path: string;
  speaker: string;
}

function App() {
  const [topic, setTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [trendingTopics, setTrendingTopics] = useState<string[]>([]);
  const [loadingTopics, setLoadingTopics] = useState(true);
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [currentAudioIndex, setCurrentAudioIndex] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSpeaker, setCurrentSpeaker] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Fetch trending topics on mount
  useEffect(() => {
    const fetchTrendingTopics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/trending-topics');
        const data = await response.json();
        setTrendingTopics(data.topics || []);
      } catch (error) {
        console.error('Error fetching trending topics:', error);
        // Set fallback topics
        setTrendingTopics([
          'Government funding',
          'Election updates',
          'Foreign policy',
          'Healthcare reform',
          'Climate policy'
        ]);
      } finally {
        setLoadingTopics(false);
      }
    };

    fetchTrendingTopics();
  }, []);

  // Fetch audio files when results are available
  useEffect(() => {
    const fetchAudioFiles = async () => {
      if (results && results.success) {
        try {
          const response = await fetch('http://localhost:8000/api/audio-files');
          const data = await response.json();
          setAudioFiles(data.audio_files || []);
        } catch (error) {
          console.error('Error fetching audio files:', error);
        }
      }
    };

    fetchAudioFiles();
  }, [results]);

  // Handle audio playback
  const playAudio = (index: number) => {
    if (audioFiles.length === 0) return;
    
    const audioFile = audioFiles[index];
    setCurrentAudioIndex(index);
    setCurrentSpeaker(audioFile.speaker);
    setIsPlaying(true);
    
    // Create audio element if it doesn't exist
    if (!audioRef.current) {
      audioRef.current = new Audio();
    }
    
    const audio = audioRef.current;
    audio.src = `http://localhost:8000${audioFile.path}`;
    audio.play();
    
    audio.onended = () => {
      // Auto-play next audio
      if (index < audioFiles.length - 1) {
        playAudio(index + 1);
      } else {
        setIsPlaying(false);
        setCurrentAudioIndex(null);
        setCurrentSpeaker(null);
      }
    };
    
    audio.onerror = () => {
      setIsPlaying(false);
      setCurrentAudioIndex(null);
      setCurrentSpeaker(null);
    };
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentAudioIndex(null);
    setCurrentSpeaker(null);
  };

  const handleTopicSelect = (selectedTopic: string) => {
    setTopic(selectedTopic);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsLoading(true);
    setResults(null); // Clear previous results
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      });
      
      const data = await response.json();
      console.log('Results:', data);
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to analyze topic');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-600 via-slate-500 to-blue-400 flex flex-col items-center justify-center px-4 py-8">
      {/* Main Content */}
      <div className="text-center mb-12 w-full max-w-4xl">
        <h1 className="text-6xl font-bold text-white mb-4 drop-shadow-lg">
          The Andrew Exchange
        </h1>
        <p className="text-white/80 text-lg mb-8">Explore both sides of today's political debates</p>
        
        {/* Trending Topics */}
        {!loadingTopics && trendingTopics.length > 0 && (
          <div className="mb-8">
            <p className="text-white/90 text-sm font-semibold mb-3 uppercase tracking-wide">Trending Topics</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {trendingTopics.map((trendingTopic, index) => (
                <button
                  key={index}
                  onClick={() => handleTopicSelect(trendingTopic)}
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-full text-sm font-medium transition-all duration-200 backdrop-blur-sm border border-white/30 hover:border-white/50"
                >
                  {trendingTopic}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {loadingTopics && (
          <div className="mb-8">
            <p className="text-white/70 text-sm">Loading trending topics...</p>
          </div>
        )}
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter a political topic..."
            className="px-6 py-3 rounded-lg bg-white text-gray-800 placeholder-gray-500 shadow-lg focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 w-64 sm:w-auto"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !topic.trim()}
            className="px-6 py-3 rounded-lg bg-slate-500 bg-opacity-70 text-white shadow-lg hover:bg-opacity-90 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>

      {/* Results Display */}
      {results && (
        <div className="w-full max-w-6xl bg-white bg-opacity-95 rounded-3xl shadow-2xl p-8 backdrop-blur-sm mb-8">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Debate Audio</h2>
            {results.script_path && (
              <p className="text-gray-600 mb-2 text-sm">
                Script saved to: <code className="text-sm bg-gray-100 px-2 py-1 rounded">{results.script_path}</code>
              </p>
            )}
          </div>
          
          {/* Audio Player Section */}
          {audioFiles.length > 0 ? (
            <div className="space-y-6">
              {/* Speaker Images Display */}
              <div className="flex justify-center items-center gap-8 mb-6">
                <div className={`text-center transition-all duration-300 ${currentSpeaker === 'CARNEGIE' ? 'scale-110' : 'opacity-50 scale-100'}`}>
                  <img 
                    src="/carnegie.jpg" 
                    alt="Andrew Carnegie" 
                    className={`w-48 h-48 rounded-full object-cover border-4 transition-all ${
                      currentSpeaker === 'CARNEGIE' 
                        ? 'border-blue-500 shadow-2xl' 
                        : 'border-gray-300 shadow-md'
                    }`}
                    onError={(e) => {
                      // Fallback to placeholder if image doesn't exist
                      (e.target as HTMLImageElement).src = 'https://via.placeholder.com/200/6496C8/FFFFFF?text=Carnegie';
                    }}
                  />
                  <p className="mt-4 text-lg font-semibold text-gray-800">Andrew Carnegie</p>
                </div>
                
                <div className={`text-center transition-all duration-300 ${currentSpeaker === 'MELLON' ? 'scale-110' : 'opacity-50 scale-100'}`}>
                  <img 
                    src="/mellon.jpg" 
                    alt="Andrew Mellon" 
                    className={`w-48 h-48 rounded-full object-cover border-4 transition-all ${
                      currentSpeaker === 'MELLON' 
                        ? 'border-red-500 shadow-2xl' 
                        : 'border-gray-300 shadow-md'
                    }`}
                    onError={(e) => {
                      // Fallback to placeholder if image doesn't exist
                      (e.target as HTMLImageElement).src = 'https://via.placeholder.com/200/EF4444/FFFFFF?text=Mellon';
                    }}
                  />
                  <p className="mt-4 text-lg font-semibold text-gray-800">Andrew Mellon</p>
                </div>
              </div>

              {/* Audio Controls */}
              <div className="flex justify-center gap-4 mb-6">
                {!isPlaying ? (
                  <button
                    onClick={() => playAudio(0)}
                    className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-lg font-semibold transition-all duration-200 flex items-center gap-2"
                  >
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                    </svg>
                    Play Debate
                  </button>
                ) : (
                  <button
                    onClick={stopAudio}
                    className="px-8 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg shadow-lg font-semibold transition-all duration-200 flex items-center gap-2"
                  >
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Stop
                  </button>
                )}
              </div>

              {/* Audio Progress */}
              {isPlaying && currentAudioIndex !== null && (
                <div className="bg-gray-100 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-2">
                    Playing segment {currentAudioIndex + 1} of {audioFiles.length}
                  </p>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((currentAudioIndex + 1) / audioFiles.length) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Audio Files List */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Audio Segments ({audioFiles.length})</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
                  {audioFiles.map((audioFile, index) => (
                    <button
                      key={index}
                      onClick={() => playAudio(index)}
                      className={`text-left p-3 rounded-lg transition-all ${
                        currentAudioIndex === index
                          ? 'bg-blue-500 text-white shadow-lg'
                          : audioFile.speaker === 'CARNEGIE'
                          ? 'bg-blue-100 hover:bg-blue-200 text-gray-800'
                          : 'bg-red-100 hover:bg-red-200 text-gray-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          Segment {index + 1} - {audioFile.speaker}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : results.error ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
              <p className="text-yellow-800 font-semibold mb-2">Warning: Script Generation Error</p>
              <p className="text-yellow-700 text-sm">{results.error}</p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-6">
              <p className="text-gray-600">No audio files found. Please generate the script first, then run the video generator to create audio files.</p>
            </div>
          )}
        </div>
      )}

      {/* Placeholder Content Grid - Show when no results */}
      {!results && !isLoading && (
        <div className="w-full max-w-6xl bg-white bg-opacity-95 rounded-3xl shadow-2xl p-8 backdrop-blur-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Placeholder Cards */}
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-4">
                <div className="h-12 bg-gray-200 rounded-lg"></div>
                <div className="h-40 bg-gray-100 rounded-lg"></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="w-full max-w-6xl bg-white bg-opacity-95 rounded-3xl shadow-2xl p-8 backdrop-blur-sm">
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-slate-600 mb-4"></div>
            <p className="text-gray-800 text-xl font-semibold mb-4">Creating Your Debate</p>
            <div className="space-y-2 text-center text-gray-600">
              <p>Analyzing political perspectives...</p>
              <p>Generating debate script...</p>
              <p>Creating audio with AI voices...</p>
              <p className="text-sm text-gray-500 mt-4">This may take 30-60 seconds</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
