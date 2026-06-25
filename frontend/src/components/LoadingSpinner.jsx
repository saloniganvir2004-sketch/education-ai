import { memo } from "react";

function LoadingSpinner({
  text = "Loading..."
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-8" role="status" aria-live="polite">
      <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" aria-hidden="true" />

      <p className="text-cyan-300 text-sm font-medium">
        {text}
      </p>
    </div>
  );
}

export default memo(LoadingSpinner);