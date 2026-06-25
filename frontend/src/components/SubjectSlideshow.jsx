import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

const SUBJECTS = [
  {
    title: "Physics Universe",
    icon: "⚛",
    description: "Energy • Motion • Space • Time"
  },
  {
    title: "Mathematics Universe",
    icon: "π",
    description: "Numbers • Graphs • Geometry"
  },
  {
    title: "History Universe",
    icon: "📜",
    description: "Civilizations • Empires • Timelines"
  },
  {
    title: "Chemistry Universe",
    icon: "🧪",
    description: "Molecules • Reactions • Elements"
  },
  {
    title: "English Literature",
    icon: "📚",
    description: "Poetry • Stories • Drama"
  },
  {
    title: "Hindi Literature",
    icon: "✍️",
    description: "कहानियाँ • कविताएँ • साहित्य"
  }
];

export default function SubjectSlideshow() {
  const [index, setIndex] = useState(0);

  const subjects = useMemo(() => SUBJECTS, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % subjects.length);
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const subject = subjects[index];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={subject.title}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 0.2, scale: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1.5 }}
        className="absolute inset-0 flex flex-col items-center justify-center text-center"
        aria-hidden="true"
      >
        <div className="text-[12rem]">
          {subject.icon}
        </div>

        <h2 className="text-5xl font-bold text-cyan-200">
          {subject.title}
        </h2>

        <p className="text-xl text-cyan-100 mt-3">
          {subject.description}
        </p>
      </motion.div>
    </AnimatePresence>
  );
}