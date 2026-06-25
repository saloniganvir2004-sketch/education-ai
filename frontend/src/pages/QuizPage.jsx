import { useCallback, useState } from "react";
import BackButton from "../components/BackButton";

export default function QuizPage() {
  const [quiz, setQuiz] = useState("");
  const [loading, setLoading] = useState(false);

  const generateQuiz = useCallback(async () => {
    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/generate-quiz"
      );
      if (!response.ok) {
        throw new Error("Failed to generate quiz.");
      }
      const data = await response.json();

      setQuiz(data.quiz || "No quiz was generated.");
    } catch (error) {
      console.error(error);
      setQuiz("Failed to generate quiz.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <BackButton />
        <div className="mb-10">
          <h1 className="text-6xl font-black">
            Quiz Generator
          </h1>

          <p className="text-slate-400 mt-3 text-xl">
            Generate AI quizzes from uploaded PDFs
          </p>
        </div>

        <button
          onClick={generateQuiz}
          className="px-8 py-4 rounded-2xl bg-cyan-500 hover:bg-cyan-400 font-bold transition"
          disabled={loading}
          aria-label="Generate Quiz"
        >
          Generate Quiz
        </button>

        {loading && (
          <div className="mt-8 text-cyan-300">
            Generating Quiz...
          </div>
        )}

        {quiz && (
          <div className="mt-8 bg-slate-900 border border-slate-800 rounded-3xl p-8 whitespace-pre-wrap">
            {quiz}
          </div>
        )}
      </div>
    </div>
  );
}