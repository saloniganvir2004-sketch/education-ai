import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";

export default function SubjectExplorerPage() {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState("");

  const handleContinue = useCallback(() => {
    localStorage.setItem("subject", selectedSubject);
    navigate("/dashboard");
  }, [navigate, selectedSubject]);

  const subjects = [
    { name: "Physics", concepts: 486, icon: "⚛️" },
    { name: "Mathematics", concepts: 622, icon: "📐" },
    { name: "Chemistry", concepts: 351, icon: "🧪" },
    { name: "History", concepts: 214, icon: "🏛️" },
    { name: "English", concepts: 173, icon: "📚" },
    { name: "Hindi", concepts: 141, icon: "🇮🇳" },
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="border-b border-slate-800 p-6">
        <h1 className="text-5xl font-black">
          Choose Your Subject
        </h1>

        <p className="text-slate-400 mt-2 text-lg">
          Select a subject to personalize your AI learning experience
        </p>
      </div>

      <div className="max-w-7xl mx-auto p-8">
        <BackButton />

        <div className="grid md:grid-cols-3 gap-6">

          {subjects.map((subject) => (
            <div
              key={subject.name}
              onClick={() => setSelectedSubject(subject.name)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  setSelectedSubject(subject.name);
                }
              }}
              aria-pressed={selectedSubject === subject.name}
              className={`cursor-pointer rounded-3xl p-8 transition border ${
                selectedSubject === subject.name
                  ? "bg-cyan-900/40 border-cyan-500"
                  : "bg-slate-900 border-slate-800 hover:border-cyan-700"
              }`}
            >
              <div className="text-5xl mb-4">
                {subject.icon}
              </div>

              <h2 className="text-2xl font-bold">
                {subject.name}
              </h2>

              <p className="text-slate-400 mt-2">
                {subject.concepts} Concepts
              </p>
            </div>
          ))}

        </div>

        {selectedSubject && (
          <div className="mt-12 bg-slate-900 border border-cyan-700 rounded-3xl p-8 text-center">
            <h2 className="text-3xl font-bold text-cyan-400">
              Selected Subject
            </h2>

            <p className="text-2xl mt-4">
              {selectedSubject}
            </p>

            <button
              onClick={handleContinue}
              aria-label={`Continue with ${selectedSubject}`}
              className="mt-6 px-10 py-4 rounded-2xl bg-cyan-500 hover:bg-cyan-400 font-bold text-lg transition"
            >
              Continue to Dashboard →
            </button>
            <button
              onClick={() => navigate("/upload")}
              className="mt-4 ml-4 px-10 py-4 rounded-2xl border border-cyan-500 hover:bg-cyan-900/30 font-bold text-lg transition"
            >
              Upload New Topic
            </button>
          </div>
        )}

      </div>
    </div>
  );
}