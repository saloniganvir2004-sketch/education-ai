import { useCallback, useState } from "react";
import BackButton from "../components/BackButton";

export default function MindMapPage() {
  const [mindmap, setMindmap] = useState("");
  const [loading, setLoading] = useState(false);

  const generateMindMap = useCallback(async () => {
    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/generate-mindmap"
      );

      if (!response.ok) {
        throw new Error("Failed to generate mind map.");
      }

      const data = await response.json();

      setMindmap(data.mindmap || "No mind map was generated.");

    } catch (error) {
      setMindmap("Failed to generate mind map.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <BackButton />

        <h1 className="text-6xl font-black mb-4">
          Mind Map Generator
        </h1>

        <p className="text-slate-400 mb-8">
          Generate AI mind maps from uploaded PDFs
        </p>

        <button
          onClick={generateMindMap}
          className="px-8 py-4 rounded-2xl bg-cyan-500 hover:bg-cyan-400 font-bold"
          disabled={loading}
          aria-label="Generate Mind Map"
        >
          Generate Mind Map
        </button>

        {loading && (
          <div className="mt-8">
            Generating Mind Map...
          </div>
        )}

        {mindmap && (
          <div className="mt-8 bg-slate-900 border border-slate-800 rounded-3xl p-8 whitespace-pre-wrap">
            {mindmap}
          </div>
        )}

      </div>
    </div>
  );
}