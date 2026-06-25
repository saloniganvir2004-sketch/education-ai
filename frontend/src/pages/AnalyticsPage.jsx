import { useEffect, useMemo, useState } from "react";
import BackButton from "../components/BackButton";

export default function AnalyticsPage() {
  const stats = useMemo(() => ([
    { value: 12, label: "Files Uploaded" },
    { value: 47, label: "Questions Asked" },
    { value: 15, label: "Quizzes Generated" },
    { value: 9, label: "Summaries Created" },
    { value: 8, label: "Mind Maps" },
  ]), []);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    const loadAnalytics = async () => {
      setLoading(true);
      try {
        // Backend analytics endpoint can be connected here.
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadAnalytics();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto">

        <BackButton />

        <div className="mb-10">
          <h1 className="text-6xl font-black">
            Learning Analytics
          </h1>

          <p className="text-slate-400 mt-3 text-xl">
            Track learning performance and AI activity{loading && " • Refreshing..."}
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-6 mb-10">

          {stats.map((item) => (
            <div key={item.label} className="bg-slate-900 rounded-3xl p-6">
              <div className="text-4xl font-bold">{item.value}</div>
              <div className="text-slate-400 mt-2">{item.label}</div>
            </div>
          ))}

        </div>

        <div className="grid lg:grid-cols-2 gap-8">

          <div className="bg-slate-900 rounded-3xl p-8">
            <h2 className="text-3xl font-bold mb-6">
              Subject Progress
            </h2>

            <div className="space-y-6">

              <div>
                <div className="flex justify-between mb-2">
                  <span>Physics</span>
                  <span>90%</span>
                </div>

                <div className="h-4 bg-slate-800 rounded-full">
                  <div className="h-4 w-[90%] bg-cyan-500 rounded-full"></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span>Mathematics</span>
                  <span>84%</span>
                </div>

                <div className="h-4 bg-slate-800 rounded-full">
                  <div className="h-4 w-[84%] bg-blue-500 rounded-full"></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span>Chemistry</span>
                  <span>76%</span>
                </div>

                <div className="h-4 bg-slate-800 rounded-full">
                  <div className="h-4 w-[76%] bg-purple-500 rounded-full"></div>
                </div>
              </div>

            </div>
          </div>

          <div className="bg-slate-900 rounded-3xl p-8">
            <h2 className="text-3xl font-bold mb-6">
              AI Activity
            </h2>

            <div className="space-y-4">

              <div className="p-4 bg-slate-800 rounded-2xl">
                Quiz Generated
              </div>

              <div className="p-4 bg-slate-800 rounded-2xl">
                Summary Created
              </div>

              <div className="p-4 bg-slate-800 rounded-2xl">
                Mind Map Generated
              </div>

              <div className="p-4 bg-slate-800 rounded-2xl">
                Architecture Generated
              </div>

              <div className="p-4 bg-slate-800 rounded-2xl">
                Chat Question Answered
              </div>

            </div>
          </div>

        </div>

      </div>
    </div>
  );
}