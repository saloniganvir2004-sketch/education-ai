import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";

export default function DashboardPage() {
  const navigate = useNavigate();

  const handleNavigate = useCallback((route) => {
    navigate(route);
  }, [navigate]);

  const currentSubject =
    localStorage.getItem("subject") || "General";

  const features = [
    {
      title: "Upload Knowledge",
      icon: "📤",
      route: "/upload",
      description: "Upload PDFs and learning resources",
    },
    {
      title: "AI Tutor",
      icon: "💬",
      route: "/chat",
      description: "Ask questions from uploaded content",
    },
    {
      title: "Quiz Generator",
      icon: "📝",
      route: "/quiz",
      description: "Generate MCQs and practice tests",
    },
    {
      title: "Summary Generator",
      icon: "📖",
      route: "/summary",
      description: "Create concise study notes",
    },
    {
      title: "Mind Map Generator",
      icon: "🧠",
      route: "/mindmap",
      description: "Visualize topic relationships",
    },
    {
      title: "Architecture Builder",
      icon: "🏗️",
      route: "/architecture",
      description: "Generate knowledge structures",
    },
    {
      title: "Learning Analytics",
      icon: "📊",
      route: "/analytics",
      description: "Track learning progress",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <BackButton />

        <div className="mb-10">
          <h1 className="text-6xl font-black">
            AI Dashboard
          </h1>

          <p className="text-slate-400 mt-3 text-xl">
            Central hub for learning, analysis and AI-powered education tools
          </p>

          <div className="mt-6 inline-block px-6 py-3 rounded-2xl bg-cyan-900/40 border border-cyan-700">
            <span className="text-cyan-300 font-semibold">
              Current Subject:
            </span>{" "}
            {currentSubject}
          </div>
        </div>

        <div className="grid md:grid-cols-4 gap-6 mb-10">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
            <div className="text-4xl font-bold">124</div>
            <div className="text-slate-400 mt-2">
              Files Uploaded
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
            <div className="text-4xl font-bold">12</div>
            <div className="text-slate-400 mt-2">
              Subjects
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
            <div className="text-4xl font-bold">486</div>
            <div className="text-slate-400 mt-2">
              Concepts
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
            <div className="text-4xl font-bold">92%</div>
            <div className="text-slate-400 mt-2">
              AI Accuracy
            </div>
          </div>
        </div>

        <h2 className="text-3xl font-bold mb-6">
          AI Learning Tools
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
          {features.map((feature) => (
            <div
              key={feature.title}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  handleNavigate(feature.route);
                }
              }}
              aria-label={feature.title}
              onClick={() => handleNavigate(feature.route)}
              className="cursor-pointer bg-slate-900 border border-slate-800 hover:border-cyan-500 hover:bg-slate-800 transition rounded-3xl p-8"
            >
              <div className="text-5xl mb-4">
                {feature.icon}
              </div>

              <h3 className="text-2xl font-bold mb-2">
                {feature.title}
              </h3>

              <p className="text-slate-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6">
          <h2 className="text-2xl font-bold mb-6">
            Recent Activity
          </h2>

          <div className="space-y-4">
            <div className="p-4 bg-slate-800 rounded-2xl">
              Physics Notes Uploaded
            </div>

            <div className="p-4 bg-slate-800 rounded-2xl">
              History PPT Processed
            </div>

            <div className="p-4 bg-slate-800 rounded-2xl">
              Quiz Generated
            </div>

            <div className="p-4 bg-slate-800 rounded-2xl">
              Architecture Created
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}