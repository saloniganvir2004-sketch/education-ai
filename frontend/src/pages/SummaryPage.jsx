import { useCallback, useState } from "react";
import BackButton from "../components/BackButton";

export default function SummaryPage() {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const generateSummary = useCallback(async () => {
    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/generate-summary"
      );

      if (!response.ok) {
        throw new Error("Failed to generate summary.");
      }

      const data = await response.json();

      setSummary(data.summary || "No summary was generated.");
    } catch (error) {
      setSummary("Failed to generate summary.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <BackButton />

        <h1 className="text-6xl font-black mb-4">
          Summary Generator
        </h1>

        <p className="text-slate-400 mb-8">
          Generate AI summaries from uploaded PDFs
        </p>

        <button
          onClick={generateSummary}
          className="px-8 py-4 rounded-2xl bg-cyan-500 hover:bg-cyan-400 font-bold"
          disabled={loading}
          aria-label="Generate Summary"
        >
          Generate Summary
        </button>

        {loading && (
          <div className="mt-8">
            Generating Summary...
          </div>
        )}

        {summary && (
          <div className="mt-8 bg-slate-900 border border-slate-800 rounded-3xl p-8 whitespace-pre-wrap">
            {summary}
          </div>
        )}

      </div>
    </div>
  );
}