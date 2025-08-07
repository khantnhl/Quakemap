import { useState, useEffect } from 'react';

export default function Card({ fileName }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    
    let isMounted = true;
    let intervalId;

    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const res = await fetch(`https://quakemap.onrender.com/result/${fileName}`);
        
        if (!isMounted) return;

        if (res.ok) {
          const data = await res.json();
          if (data && Object.keys(data).length > 0) {
            setAnalysis(data);
            setLoading(false);
            if (intervalId) clearInterval(intervalId);
          } else {
            // Still processing, continue polling
            setLoading(true);
          }
        } else if (res.status === 404 || res.status === 202) {
          
        // 404: Not found yet (still processing)
        // 202: Accepted but not ready
          setLoading(true);
        } else {
          throw new Error(`Server error: ${res.status}`);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('Fetch error:', err);
        setError(`Failed to fetch analysis: ${err.message}`);
        setLoading(false);
        if (intervalId) clearInterval(intervalId);
      }
    };

    // Start polling
    setLoading(true);
    fetchAnalysis();
    
    intervalId = setInterval(() => {
      if (!analysis && !error && isMounted) {
        fetchAnalysis();
      }
    }, 3000); // Poll every 3 seconds

    return () => {
      isMounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [fileName, analysis, error]);


  return (
    <div className="mt-6 max-w-md mx-auto p-4 border rounded-lg shadow-md bg-white">
      <h3 className="text-lg font-semibold mb-4">Analysis Result</h3>
      
      {loading && !analysis && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-500">Processing analysis...</p>
          <p className="text-xs text-gray-400">This may take a few moments</p>
        </div>
      )}
      
      {error && (
        <div className="text-center py-4">
          <p className="text-red-500">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-2 px-4 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      )}

      {analysis && (
        <div className="space-y-3">
          {analysis.map_url && (
            <div className="w-full">
              <img
                src={analysis.map_url}
                alt="Seismic intensity map"
                className="w-full h-auto rounded border shadow-sm"
                onError={(e) => {
                  e.target.style.display = 'none';
                  setError('Failed to load map image');
                }}
              />
            </div>
          )}
          
          <div className="bg-gray-50 p-3 rounded">
            <p className="text-sm"><span className="font-medium">Blob:</span> {fileName}</p>
            {analysis.mmi_estimation && (
              <p className="text-sm"><span className="font-medium">MMI Estimation:</span> {analysis.mmi_estimation}</p>
            )}
            {analysis.confidence && (
              <p className="text-sm"><span className="font-medium">Confidence:</span> {(analysis.confidence * 100).toFixed(1)}%</p>
            )}
          </div>
          
          {analysis.reasoning && (
            <div className="mt-3">
              <h4 className="font-medium text-sm">Reasoning:</h4>
              <p className="text-xs text-gray-700 mt-1 bg-gray-50 p-2 rounded whitespace-pre-wrap">
                {analysis.reasoning}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}