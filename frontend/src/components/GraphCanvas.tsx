"use client";

import { useRef, useEffect, useMemo, useCallback, memo } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";

const NODE_COLORS: Record<string, string> = {
  user_role:       "#00F0FF",
  agent:           "#a78bfa",
  capability:      "#4ade80",
  sensitive_data:  "#fb923c",
  guardrail:       "#facc15",
  attack_surface:  "#f87171",
};

interface Props {
  graphData: { nodes: unknown[]; edges: unknown[] };
}

function GraphCanvas({ graphData }: Props) {
  const fgRef = useRef<ReturnType<typeof ForceGraph3D> | null>(null);

  // Gentle camera pull-back after load
  useEffect(() => {
    const t = setTimeout(() => {
      if (fgRef.current) {
        (fgRef.current as { cameraPosition: (pos: object, look: object, ms: number) => void })
          .cameraPosition({ z: 400 }, { x: 0, y: 0, z: 0 }, 1500);
      }
    }, 600);
    return () => clearTimeout(t);
  }, []);

  // Memoize parsed graph data so ForceGraph3D doesn't re-initialize on parent re-renders
  const fgData = useMemo(() => {
    const nodes = (graphData.nodes as Record<string, unknown>[]).map((n) => ({
      ...n,
      id: n.id,
      name: n.label,
      color: NODE_COLORS[n.type as string] ?? "#64748b",
    }));

    const links = (graphData.edges as Record<string, unknown>[]).map((e) => ({
      source: e.source,
      target: e.target,
      label: e.type,
    }));

    return { nodes, links };
  }, [graphData]);

  const nodeColorFn = useCallback(
    (n: Record<string, unknown>) => String(n.color ?? "#64748b"),
    []
  );

  const nodeThreeObjectFn = useCallback((n: Record<string, unknown>) => {
    const color = String(n.color ?? "#64748b");
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 48;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = color;
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(n.name ?? ""), 64, 32);

    const sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: new THREE.CanvasTexture(canvas),
        transparent: true,
      })
    );
    sprite.scale.set(40, 15, 1);
    sprite.position.set(0, 12, 0);

    const group = new THREE.Group();
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(5, 16, 16),
      new THREE.MeshPhongMaterial({ color, transparent: true, opacity: 0.9 })
    );
    group.add(sphere, sprite);
    return group;
  }, []);

  const linkColorFn = useCallback(() => "rgba(255,255,255,0.65)", []);

  return (
    <ForceGraph3D
      ref={fgRef}
      graphData={fgData}
      backgroundColor="#050508"
      nodeLabel="name"
      nodeColor={nodeColorFn}
      nodeRelSize={5}
      nodeThreeObject={nodeThreeObjectFn}
      linkColor={linkColorFn}
      linkWidth={1.5}
      linkDirectionalArrowLength={4}
      linkDirectionalArrowRelPos={1}
      linkLabel="label"
      enableNodeDrag
      enableNavigationControls
    />
  );
}

export default memo(GraphCanvas);
