import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

export default function BackButton() {
  const navigate = useNavigate();

  const handleBack = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  return (
    <button
      onClick={handleBack}
      aria-label="Go Back"
      type="button"
      className="mb-6 px-5 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 transition"
    >
      ← Back
    </button>
  );
}