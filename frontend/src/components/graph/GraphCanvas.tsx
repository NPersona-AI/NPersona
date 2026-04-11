"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useMemo, useCallback } from "react";
import * as THREE from "three";
import { colors } from "@/lib/colors";
import SpriteText from 'three-spritetext';

const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });

export default function GraphCanvas({ graphData }: { graphData: any }) {
  const fgRef = useRef<any>(null);
  const [hoverNode, setHoverNode] = useState<any>(null);

  // Parse backend graph data into force-graph format
  const parsedData = useMemo(() => {
    if (!graphData || !graphData.nodes) return { nodes: [], links: [] };
    
    return {
      nodes: graphData.nodes.map((n: any) => ({
        ...n,
        // color and size are mapped from backend
        val: n.size * 5, // visually scale size
      })),
      links: graphData.edges.map((e: any) => ({
        ...e,
        // force-graph uses source and target 
      })),
    };
  }, [graphData]);

  const handleNodeClick = useCallback((node: any) => {
    // Focus camera on node
    const distance = 60;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

    if (fgRef.current) {
      fgRef.current.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        3000
      );
    }
  }, []);

  // Stable nodeThreeObject — no hoverNode dependency so the graph never
  // rebuilds its 3D objects on hover/click. Hover highlight is handled by
  // the nodeColor prop instead (which does per-frame color updates cheaply).
  const nodeThreeObjectFn = useCallback((node: any) => {
    const group = new THREE.Group();

    const geometry = new THREE.SphereGeometry(node.val, 16, 16);
    const material = new THREE.MeshLambertMaterial({
      color: node.color,
      emissive: node.color,
      emissiveIntensity: 0.4,
    });
    const sphere = new THREE.Mesh(geometry, material);
    group.add(sphere);

    if (node.val > 5) {
      const sprite = new SpriteText(node.label);
      sprite.color = "white";
      sprite.textHeight = 4;
      sprite.position.set(0, node.val + 5, 0);
      group.add(sprite);
    }

    return group;
  }, []);

  return (
    <div className="absolute inset-0 bg-[#0a0a0f]">
      {typeof window !== "undefined" && (
        <ForceGraph3D
          ref={fgRef}
          graphData={parsedData}
          nodeLabel={(node: any) => `
            <div style="background: rgba(0,0,0,0.8); padding: 8px; border-radius: 4px; border: 1px solid ${node.color}; pointer-events: none;">
              <div style="font-weight: bold; color: ${node.color}">${node.label}</div>
              <div style="font-size: 10px; color: #aaa">${node.type}</div>
            </div>
          `}
          nodeColor={(node: any) => hoverNode === node ? "#fff" : (node.color || "#fff")}
          nodeRelSize={2}
          onNodeHover={setHoverNode}
          onNodeClick={handleNodeClick}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={1.5}
          linkDirectionalParticleColor={() => "#ffffff"}
          linkDirectionalParticleSpeed={0.005}
          linkColor={(link: any) => {
            // Find source node color if possible, fallback to white/gray
            const sourceNode = parsedData.nodes.find((n: any) => n.id === link.source || n.id === link.source?.id);
            return sourceNode?.color ? `${sourceNode.color}66` : "rgba(255,255,255,0.2)";
          }}
          linkOpacity={0.3}
          backgroundColor="#0a0a0f"
          nodeThreeObject={nodeThreeObjectFn}
        />
      )}
    </div>
  );
}
