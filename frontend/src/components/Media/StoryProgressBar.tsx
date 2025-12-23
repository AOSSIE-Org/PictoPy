import { motion } from 'framer-motion';

interface StoryProgressBarProps {
  total: number;
  current: number;
  duration?: number;
  paused?: boolean;
}

export function StoryProgressBar({
  total,
  current,
  duration = 4000,
  paused = false,
}: StoryProgressBarProps) {
  return (
    <div className="absolute top-27 left-1/2 z-50 flex w-[70%] -translate-x-1/2 justify-center gap-1">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className="h-[2px] w-10 overflow-hidden rounded-full bg-white/30"
        >
          {i < current && <div className="h-full w-full bg-white" />}

          {i === current && (
            <motion.div
              className="h-full bg-white"
              initial={{ width: '0%' }}
              animate={{ width: paused ? '0%' : '100%' }}
              transition={{
                duration: paused ? 0 : duration / 1000,
                ease: 'linear',
              }}
            />
          )}
        </div>
      ))}
    </div>
  );
}
