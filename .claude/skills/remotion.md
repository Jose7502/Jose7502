# Remotion Video Generation Skill

Use this skill to generate videos programmatically using [Remotion](https://www.remotion.dev/), a framework for creating videos with React and TypeScript.

## Trigger

Invoke with `/remotion` or when the user asks to:
- Generate or create a video
- Render an animation or motion graphic
- Build a programmatic video
- Create video content with React/TypeScript

## Instructions

When this skill is invoked:

1. **Understand the video requirements**: Ask for or infer:
   - Video dimensions (default: 1920x1080)
   - Duration in frames (default: 30fps)
   - Visual content, animations, or data to display

2. **Generate Remotion components** following this structure:
   ```
   remotion/
   ├── package.json
   ├── src/
   │   ├── Root.tsx          # Register all compositions
   │   ├── index.ts          # Entry point
   │   └── videos/           # Video components
   │       └── MyVideo.tsx
   └── remotion.config.ts    # Remotion configuration
   ```

3. **Component template**:
   ```tsx
   import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';

   export const MyVideo: React.FC = () => {
     const frame = useCurrentFrame();
     const opacity = interpolate(frame, [0, 30], [0, 1]);
     return (
       <AbsoluteFill style={{ backgroundColor: 'white', opacity }}>
         {/* content */}
       </AbsoluteFill>
     );
   };
   ```

4. **Register in Root.tsx**:
   ```tsx
   import { Composition } from 'remotion';
   import { MyVideo } from './videos/MyVideo';

   export const RemotionRoot: React.FC = () => (
     <>
       <Composition
         id="MyVideo"
         component={MyVideo}
         durationInFrames={150}
         fps={30}
         width={1920}
         height={1080}
       />
     </>
   );
   ```

5. **Render commands**:
   - Preview: `npx remotion studio`
   - Render video: `npx remotion render MyVideo out/video.mp4`
   - Render still: `npx remotion still MyVideo out/still.png`

## Key Remotion APIs

- `useCurrentFrame()` — current frame number
- `interpolate(frame, [in], [out])` — animate values over time
- `spring({ frame, fps })` — spring physics animations
- `Sequence` — time-offset child components
- `Audio`, `Video`, `Img` — media components
- `AbsoluteFill` — full-size container
- `useVideoConfig()` — access fps, width, height, durationInFrames

## Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "remotion": "^4.0.0",
    "@remotion/cli": "^4.0.0",
    "@remotion/renderer": "^4.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0"
  }
}
```

## Best Practices

- Use `interpolate` with `extrapolateLeft: 'clamp'` and `extrapolateRight: 'clamp'` to avoid out-of-range values
- Keep compositions modular — one component per scene
- Use `Sequence` to compose scenes in a timeline
- Leverage CSS-in-JS (inline styles) for styling — no CSS files needed
- Use `spring()` for natural-feeling animations
