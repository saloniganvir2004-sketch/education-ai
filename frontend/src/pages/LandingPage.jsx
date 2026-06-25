import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import PhysicsScene from "../scenes/PhysicsScene";

export default function LandingPage() {
  const navigate = useNavigate();
  const handleStartLearning = useCallback(() => {
    navigate("/subjects");
  }, [navigate]);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <PhysicsScene />

      <div className="absolute inset-0 bg-black/30" />

      <div className="absolute inset-0 z-20 flex items-center justify-center px-6">
        <div className="backdrop-blur-xl bg-white/10 border border-cyan-400/30 rounded-3xl px-12 py-12 text-center max-w-4xl">

          <h1 className="text-7xl font-extrabold text-cyan-300 drop-shadow-lg">
            Education AI
          </h1>

          <p className="mt-6 text-2xl text-white">
            Learn Anything. Explore Everything.
          </p>

          <p className="mt-4 text-cyan-100 text-lg">
            Upload notes, generate quizzes, create summaries,
            build mind maps, visualize architectures and learn
            with an AI-powered education platform.
          </p>

          <div className="mt-10">
            <button
              onClick={handleStartLearning}
              aria-label="Start Learning"
              className="px-10 py-4 rounded-2xl bg-cyan-500 hover:bg-cyan-400 transition font-bold text-lg"
            >
              Start Learning
            </button>
          </div>

          <div className="mt-12 grid md:grid-cols-4 gap-4">

            <div className="bg-white/10 rounded-2xl p-4">
              <div className="text-3xl mb-2">📤</div>
              <div className="font-semibold">Upload Notes</div>
            </div>

            <div className="bg-white/10 rounded-2xl p-4">
              <div className="text-3xl mb-2">💬</div>
              <div className="font-semibold">AI Tutor</div>
            </div>

            <div className="bg-white/10 rounded-2xl p-4">
              <div className="text-3xl mb-2">📝</div>
              <div className="font-semibold">Quiz Generator</div>
            </div>

            <div className="bg-white/10 rounded-2xl p-4">
              <div className="text-3xl mb-2">🧠</div>
              <div className="font-semibold">Mind Maps</div>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}