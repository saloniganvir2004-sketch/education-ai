import { useMemo } from "react";
export default function FloatingParticles() {
  const particles = useMemo(() => ([
    "absolute top-20 left-20 w-4 h-4 bg-cyan-400 rounded-full animate-ping",
    "absolute top-40 right-40 w-3 h-3 bg-blue-400 rounded-full animate-pulse",
    "absolute bottom-40 left-1/4 w-5 h-5 bg-cyan-300 rounded-full animate-bounce",
    "absolute bottom-20 right-1/4 w-4 h-4 bg-blue-300 rounded-full animate-pulse",
  ]), []);
  return (
    <>
      {particles.map((className, index) => (
        <div
          key={index}
          className={className}
          aria-hidden="true"
        />
      ))}
    </>
  );
}