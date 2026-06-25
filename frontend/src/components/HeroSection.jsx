export default function HeroSection() {
  return (
    <div className="relative z-20 flex min-h-screen items-center justify-center px-6">

      <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-10 max-w-4xl text-center">

        <h1 className="text-7xl font-extrabold bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
          Education AI
        </h1>

        <p className="mt-6 text-xl text-slate-200">
          Transform learning with AI-powered educational intelligence.
        </p>

        <div className="mt-10 flex justify-center gap-4">

          <button className="px-8 py-4 rounded-xl bg-cyan-400 text-black font-bold">
            Get Started
          </button>

          <button className="px-8 py-4 rounded-xl border border-cyan-300 text-cyan-200">
            Explore
          </button>

        </div>

      </div>

    </div>
  );
}