import { useMemo, useEffect, useState } from "react";

import PhysicsScene from "../scenes/PhysicsScene";
import MathScene from "../scenes/MathScene";
import BiologyScene from "../scenes/BiologyScene";
import HistoryScene from "../scenes/HistoryScene";
import ChemistryScene from "../scenes/ChemistryScene";
import EnglishScene from "../scenes/EnglishScene";
import HindiScene from "../scenes/HindiScene";

const scenes = [
  PhysicsScene,
  MathScene,
  BiologyScene,
  HistoryScene,
  ChemistryScene,
  EnglishScene,
  HindiScene,
];

export default function SceneManager() {
  const [currentScene, setCurrentScene] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentScene((prev) => (prev + 1) % scenes.length);
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  const SceneComponent = useMemo(
    () => scenes[currentScene],
    [currentScene]
  );

  return <SceneComponent />;
}