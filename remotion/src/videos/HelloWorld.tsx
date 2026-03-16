import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const HelloWorld: React.FC<{ message?: string }> = ({
  message = "Hello, World!",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, config: { damping: 10 } });
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          fontSize: 80,
          fontWeight: "bold",
          color: "#e94560",
          transform: `scale(${scale})`,
          opacity,
          fontFamily: "sans-serif",
          textAlign: "center",
          padding: "0 60px",
        }}
      >
        {message}
      </div>
    </AbsoluteFill>
  );
};
