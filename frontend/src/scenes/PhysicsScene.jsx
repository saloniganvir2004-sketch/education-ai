import { Canvas, useFrame } from "@react-three/fiber";
import {
  OrbitControls,
  Stars,
  Sparkles,
  Float,
} from "@react-three/drei";
import { useMemo, useRef } from "react";
import Effects from "../components/Effects";

function Sun() {
  const ref = useRef();

  useFrame(() => {
    if (ref.current) ref.current.rotation.y += 0.002;
  });

  return (
    <Float speed={2} floatIntensity={1}>
      <mesh ref={ref}>
        <sphereGeometry args={[3.5, 128, 128]} />
        <meshStandardMaterial
          color="#fbbf24"
          emissive="#f97316"
          emissiveIntensity={20}
        />
      </mesh>
    </Float>
  );
}

function Planet({ radius, speed, size, color, emissive }) {
  const ref = useRef();

  useFrame(({ clock }) => {
    if (!ref.current) return;

    const t = clock.getElapsedTime() * speed;

    ref.current.position.x = Math.cos(t) * radius;
    ref.current.position.z = Math.sin(t) * radius;

    ref.current.rotation.y += 0.005;
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[size, 128, 128]} />
      <meshStandardMaterial
        color={color}
        emissive={emissive}
        emissiveIntensity={0.6}
      />
    </mesh>
  );
}

function Saturn() {
  const group = useRef();

  useFrame(({ clock }) => {
    if (!group.current) return;

    const t = clock.getElapsedTime() * 0.12;

    group.current.position.x = Math.cos(t) * 18;
    group.current.position.z = Math.sin(t) * 18;

    group.current.rotation.y += 0.002;
  });

  return (
    <group ref={group}>
      <mesh>
        <sphereGeometry args={[1.8, 128, 128]} />
        <meshStandardMaterial
          color="#e7c999"
          emissive="#8b7355"
          emissiveIntensity={0.3}
        />
      </mesh>

      <mesh rotation={[Math.PI / 2.4, 0, 0]}>
        <torusGeometry args={[3.2, 0.18, 32, 300]} />
        <meshBasicMaterial color="#f5deb3" />
      </mesh>
    </group>
  );
}

function EnergySphere() {
  const ref = useRef();

  useFrame(({ clock }) => {
    if (!ref.current) return;

    const scale =
      1 + Math.sin(clock.getElapsedTime() * 1.5) * 0.08;

    ref.current.scale.set(scale, scale, scale);

    ref.current.rotation.y += 0.001;
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[6, 64, 64]} />

      <meshBasicMaterial
        color="#22d3ee"
        wireframe
        transparent
        opacity={0.12}
      />
    </mesh>
  );
}

export default function PhysicsScene() {
  const camera = useMemo(() => ({ position: [0, 0, 16], fov: 75 }), []);
  return (
    <div className="absolute inset-0">
      <Canvas camera={camera} fallback={<div className="text-white">Loading 3D scene...</div>}>
        <color attach="background" args={["#071b34"]} />

        <Effects />

        <ambientLight intensity={4} />

        <pointLight
          position={[0, 0, 0]}
          intensity={35}
          color="#fbbf24"
        />

        <pointLight
          position={[10, 10, 10]}
          intensity={8}
          color="#22d3ee"
        />

        <Stars
          radius={500}
          depth={200}
          count={70000}
          factor={20}
          fade
        />

        <Sparkles
          count={1200}
          scale={120}
          size={8}
          speed={0.5}
          color="#67e8f9"
        />

        <EnergySphere />

        <Sun />

        {/* Earth */}
        <Planet
          radius={8}
          speed={0.35}
          size={1.4}
          color="#60a5fa"
          emissive="#2563eb"
        />

        {/* Mars */}
        <Planet
          radius={12}
          speed={0.22}
          size={1.1}
          color="#ef4444"
          emissive="#7f1d1d"
        />

        {/* Jupiter */}
        <Planet
          radius={15}
          speed={0.16}
          size={2.4}
          color="#f59e0b"
          emissive="#92400e"
        />

        <Saturn />

        <OrbitControls
          enableZoom={false}
          autoRotate
          autoRotateSpeed={0.1}
        />
      </Canvas>
    </div>
  );
}