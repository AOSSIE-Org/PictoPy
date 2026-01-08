import { motion } from "framer-motion";
import { ImageIcon, FolderSync, Search, Code } from "lucide-react";

export default function TechMarquee() {
  const technologies = [
    { text: "PictoAI", icon: <ImageIcon className="inline-block ml-1 text-green-500" /> },
    { text: "SmartSort", icon: <FolderSync className="inline-block ml-1 text-yellow-500" /> },
    { text: "QuickView", icon: <Search className="inline-block ml-1 text-green-500" /> },
    { text: "CodeAI", icon: <Code className="inline-block ml-1 text-yellow-500" /> },
  ];
// Repeat the original list 8-10 times to prevent any visible gap on different screen sizes
  const repeatedTechnologies = Array(10).fill(technologies).flat();

  return (
    <div className="relative w-full overflow-hidden bg-white dark:bg-black py-4">
      <motion.div
        className="flex items-center whitespace-nowrap"
        initial={{ x: "0%" }}
        animate={{ x: "-50%" }}  // Exactly half way because we duplicated even number of times
        transition={{
          duration: 50,           // Speed control – zyada number = slow
          ease: "linear",
          repeat: Infinity,
        }}
      >
        {repeatedTechnologies.map((tech, index) => (
          <div
            key={`${index}-${tech.text}`}  // Better key for React
            className="flex-shrink-0 flex items-center mx-4 text-gray-600 dark:text-gray-300 text-xs font-medium"
          >
            <motion.span
              className="flex items-center bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 px-4 py-1.5 rounded-full transition-all duration-300 border border-gray-200 dark:border-white/10 shadow-sm"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {tech.text}
              <span className="ml-2 opacity-70">{tech.icon}</span>
            </motion.span>
            <span className="mx-6 text-gray-300 dark:text-gray-600">•</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
}