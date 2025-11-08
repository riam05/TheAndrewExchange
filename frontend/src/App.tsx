import React, { useState, useEffect } from 'react';

interface AnalysisResult {
  success: boolean;
  script?: string;
  script_path?: string;
  debate_data?: any;
  data?: any;
  saved_to: string;
  error?: string;
}

function App() {
  const [topic, setTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [trendingTopics, setTrendingTopics] = useState<string[]>([]);
  const [loadingTopics, setLoadingTopics] = useState(true);

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
          Political Debate Analyzer
        </h1>
        <p className="text-white/80 text-lg mb-8">Explore both sides of today's political debates</p>
        
        {/* Trending Topics */}
        {!loadingTopics && trendingTopics.length > 0 && (
          <div className="mb-8">
            <p className="text-white/90 text-sm font-semibold mb-3 uppercase tracking-wide">🔥 Trending Topics</p>
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
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Debate Script</h2>
            {results.script_path && (
              <p className="text-gray-600 mb-2">
                Script saved to: <code className="text-sm bg-gray-100 px-2 py-1 rounded">{results.script_path}</code>
              </p>
            )}
            {results.saved_to && (
              <p className="text-gray-600 text-sm">
                Data saved to: <code className="text-sm bg-gray-100 px-2 py-1 rounded">{results.saved_to}</code>
              </p>
            )}
          </div>
          
          {results.script ? (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-8 overflow-auto max-h-[600px] border border-blue-200">
              <div className="space-y-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <h3 className="text-lg font-semibold text-gray-800">Carnegie vs Mellon Debate</h3>
                </div>
                <div className="bg-white rounded-lg p-6 shadow-sm">
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap break-words font-sans leading-relaxed">
                    {results.script}
                  </pre>
                </div>
              </div>
            </div>
          ) : results.error ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
              <p className="text-yellow-800 font-semibold mb-2">⚠️ Script Generation Error</p>
              <p className="text-yellow-700 text-sm">{results.error}</p>
              {results.data && (
                <div className="mt-4 bg-gray-50 rounded-xl p-4 overflow-auto max-h-[400px]">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Raw Data:</p>
                  <pre className="text-xs text-gray-800 whitespace-pre-wrap break-words">
                    {JSON.stringify(results.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-6 overflow-auto max-h-[600px]">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap break-words">
                {JSON.stringify(results.data, null, 2)}
              </pre>
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
            <p className="text-gray-600 text-lg">Generating debate script...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
