
import { motion, useAnimation } from "framer-motion";
import { ImageIcon, FolderSync, Search, Code } from "lucide-react";
import { useState, useEffect } from "react";

export default function TechMarquee() {
  const [isHovered, setIsHovered] = useState(false);
  const controls = useAnimation();
  const technologies = [
    { 
      text: "PictoAI", 
      icon: <ImageIcon className="inline-block ml-1 text-green-500" />,
    },
    { 
      text: "SmartSort", 
      icon: <FolderSync className="inline-block ml-1 text-yellow-500" />,
    },
    { 
      text: "QuickView", 
      icon: <Search className="inline-block ml-1 text-green-500" />,
    },
    { 
      text: "CodeAI", 
      icon: <Code className="inline-block ml-1 text-yellow-500" />,
    }
  ];

  useEffect(() => {
    if (!isHovered) {
      controls.start({
        x: '-50%',
        transition: {
          duration: 10,
          ease: "linear",
          repeat: Infinity,
          repeatType: "loop"
        }
      });
    } else {
      controls.stop();
    }
  }, [isHovered, controls]);

  return (
    <div className="relative w-full overflow-hidden 
        bg-white 
        dark:bg-black
        py-4 
        dark:shadow-[0_0_50px_rgba(255,255,255,0.1)]
        transition-shadow duration-500
        z-10"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        >
      <motion.div
        className="flex space-x-6 items-center will-change-transform"
        initial={{ x: '0%' }}
        animate={controls}
      >
        {[...technologies, ...technologies, ...technologies, ...technologies, ...technologies, ...technologies].map((tech, index) => (
          <div
            key={index}
            className="flex-shrink-0 flex items-center text-gray-600 dark:text-gray-300 text-xs font-medium relative z-10"
          >
            <motion.span 
              className="flex items-center 
                bg-gray-100 dark:bg-white/5
                hover:bg-gray-200 dark:hover:bg-white/10
                px-3 py-1 
                rounded-full 
                transition-all duration-300
                border border-gray-200 dark:border-white/10
                shadow-sm
                relative z-20
                cursor-pointer"
              whileHover={{ 
                scale: 1.05,
                transition: { duration: 0.2 }
              }}
              whileTap={{ scale: 0.95 }}
            >
              {tech.text}
              <span className="ml-2 opacity-70">
                {tech.icon}
              </span>
            </motion.span>
            <span className="mx-3 text-gray-300 dark:text-gray-600">•</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
}