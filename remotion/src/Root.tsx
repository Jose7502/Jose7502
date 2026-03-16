import React from "react";
import { Composition } from "remotion";
import { HelloWorld } from "./videos/HelloWorld";
import { TextAnimation } from "./videos/TextAnimation";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ message: "Hello, World!" }}
      />
      <Composition
        id="TextAnimation"
        component={TextAnimation}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
