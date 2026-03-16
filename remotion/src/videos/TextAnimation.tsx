import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  useCurrentFrame,
} from "remotion";

interface TextSlide {
  text: string;
  color?: string;
}

const Slide: React.FC<TextSlide> = ({ text, color = "#ffffff" }) => {
  const frame = useCurrentFrame();

  const translateY = interpolate(frame, [0, 20], [60, 0], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <p
        style={{
          fontSize: 70,
          fontWeight: "bold",
          color,
          fontFamily: "sans-serif",
          transform: `translateY(${translateY}px)`,
          opacity,
          margin: 0,
          textAlign: "center",
          padding: "0 80px",
        }}
      >
        {text}
      </p>
    </AbsoluteFill>
  );
};

export const TextAnimation: React.FC = () => {
  const slides: TextSlide[] = [
    { text: "Create videos", color: "#e94560" },
    { text: "with React", color: "#0f3460" },
    { text: "using Remotion", color: "#533483" },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "#16213e" }}>
      {slides.map((slide, i) => (
        <Sequence key={i} from={i * 60} durationInFrames={60}>
          <Slide {...slide} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
