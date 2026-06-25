import { useMemo } from "react";
import { EffectComposer, Bloom } from "@react-three/postprocessing";

export default function Effects() {
  const bloomProps = useMemo(() => ({
    intensity: 2.5,
    luminanceThreshold: 0.2,
    luminanceSmoothing: 0.9,
  }), []);

  return (
    <EffectComposer>
      <Bloom
        {...bloomProps}
        mipmapBlur
      />
    </EffectComposer>
  );
}
