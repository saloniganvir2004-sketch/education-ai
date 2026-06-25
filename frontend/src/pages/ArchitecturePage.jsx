import { useCallback, useState } from "react";
import BackButton from "../components/BackButton";

export default function ArchitecturePage() {
  const [architecture, setArchitecture] = useState("");
  const [loading, setLoading] = useState(false);

  const generateArchitecture = useCallback(async () => {
    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/generate-architecture"
      );
      if (!response.ok) {
        throw new Error("Failed to generate architecture.");
      }
      const data = await response.json();

      setArchitecture(data.architecture || "No architecture was generated.");
    } catch (error) {
      console.error(error);
      setArchitecture("Failed to generate architecture.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <BackButton />

        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-6xl font-black">
              Knowledge Architecture
            </h1>

            <p className="text-slate-400 mt-3 text-xl">
              AI generated learning structure and concept relationships
            </p>
          </div>

          <button
            onClick={generateArchitecture}
            className="px-6 py-4 rounded-2xl bg-cyan-600 hover:bg-cyan-500 font-bold transition"
            disabled={loading}
            aria-label="Generate Architecture"
          >
            Generate Architecture
          </button>
        </div>

        {loading && (
          <div className="bg-slate-900 rounded-3xl p-8 text-cyan-300">
            Generating Architecture...
          </div>
        )}

        {architecture && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 whitespace-pre-wrap text-lg">
            {architecture}
          </div>
        )}
      </div>
    </div>
  );
}