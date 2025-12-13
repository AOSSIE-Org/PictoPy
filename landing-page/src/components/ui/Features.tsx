
import { motion } from "framer-motion";
import { Brain, Lightbulb, Users, TrendingUp, Target, Phone, Shield } from "lucide-react";
import type { ReactNode } from "react";
import karnx from "@/assets/karnx.png";

// Define the Feature type
type Feature = {
  icon: ReactNode;
  title: string;
  description: string;
  details: string;
  size?: "large" | "medium" | "small"; // Optional size property
};

// Define the features array
const features: Feature[] = [
  {
    icon: <Brain className="w-10 h-10" />,
    title: "AI-Powered Debates",
    description: "Engage in thought-provoking debates with our advanced AI system.",
    details: "Our AI uses state-of-the-art natural language processing to understand context and provide relevant counterarguments.",
    size: "large",
  },
  {
    icon: <Lightbulb className="w-10 h-10" />,
    title: "Improve Critical Thinking",
    description: "Sharpen your analytical skills through challenging discussions.",
    details: "Track your progress and receive personalized feedback on your critical thinking skills.",
    size: "medium",
  },
  {
    icon: <Users className="w-10 h-10" />,
    title: "Community Challenges",
    description: "Participate in community-wide debate challenges and competitions.",
    details: "Join tournaments and compete with users worldwide.",
    size: "small",
  },
  {
    icon: <TrendingUp className="w-10 h-10" />,
    title: "Track Your Progress",
    description: "Monitor your improvement with detailed performance analytics.",
    details: "View statistics on argument strength and logical consistency.",
    size: "medium",
  },
  {
    icon: <Target className="w-10 h-10" />,
    title: "Personalized Learning",
    description: "Tailored debate topics based on your interests and skill level.",
    details: "AI adapts to your learning pace and debate style.",
    size: "small",
  },
];

// FeatureCard component
import { useRef, useState, useEffect } from "react";
import { motion } from "framer-motion";

// Assuming Feature type is defined elsewhere or imported
// interface Feature { ... }

const FeatureCard = ({ feature }: { feature: Feature }) => {
  const sizeClasses = {
    large: "md:col-span-2",
    medium: "md:col-span-2",
    small: "md:col-span-1",
  };

  const sizeClass = sizeClasses[feature.size || "small"];

  const hoverTimer = useRef<number | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  // Clean Up: Detect touch capability safely for SSR/Hybrid devices
  // Ideally, rely on the delay logic, but this prevents touch-emulation triggers
  const isTouchDevice = () => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(hover: none)").matches;
  };

  const handleMouseEnter = () => {
    if (isTouchDevice()) return;

    // Logic: Only trigger state after 1 second of "intent"
    hoverTimer.current = window.setTimeout(() => {
      setIsHovered(true);
    }, 1000); 
  };

  const handleMouseLeave = () => {
    if (hoverTimer.current) {
      clearTimeout(hoverTimer.current);
      hoverTimer.current = null;
    }
    setIsHovered(false);
  };

  return (
    <motion.div
      className={`group ${sizeClass} h-full`}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      // Scale is controlled by state, ensuring it syncs with the delay
      animate={isHovered ? { scale: 1.02 } : { scale: 1 }}
      transition={{ duration: 0.3 }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div
        // CHANGED: Removed 'hover:border-...' and 'hover:shadow-...'
        // Moved styling to the conditional string below to prevent instant flashing.
        className={`relative h-full rounded-2xl bg-white dark:bg-[#161717] 
        border-2 p-6 transition-all duration-300 cursor-pointer
        ${
          isHovered
            ? "border-blue-600 shadow-[0_0_15px_rgba(30,64,175,0.9)] dark:shadow-[0_0_22px_rgba(30,64,179,1)]"
            : "border-transparent"
        }`}
      >
        <div className="mb-4 text-gray-800 dark:text-gray-200">
          {feature.icon}
        </div>
        <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">
          {feature.title}
        </h3>
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          {feature.description}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {feature.details}
        </p>
      </div>
    </motion.div>
  );
};

// DownloadCard component
const DownloadCard = () => {
  return (
    <motion.div
      className="max-w-6xl mx-auto mt-16 bg-white dark:bg-[#161717] rounded-3xl overflow-hidden"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      <div className="grid md:grid-cols-2 gap-8 p-8 md:p-12 items-center">
        {/* Left Content */}
        <div className="space-y-6">
          <motion.h2
            className="text-4xl font-bold text-gray-900 dark:text-gray-100"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            Download Our Mobile App
          </motion.h2>

          <p className="text-xl text-gray-600 dark:text-gray-300">
            Take the power of AI debates anywhere. Practice critical thinking skills on the go.
          </p>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-blue-600" />
              <span className="text-gray-700 dark:text-gray-200">Secure and private discussions</span>
            </div>
            <div className="flex items-center gap-3">
              <Phone className="w-6 h-6 text-blue-600" />
              <span className="text-gray-700 dark:text-gray-200">Available offline mode</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 pt-4">
            <button className="flex items-center gap-2 bg-black text-white px-6 py-3 rounded-xl hover:bg-gray-800 transition-colors">
              <div className="text-left">
                <div className="text-xs">Get it on</div>
                <div className="text-lg font-semibold">Google PlayStore</div>
              </div>
            </button>
          </div>
        </div>

        {/* Right Content - Phone Mockup */}
        <div className="relative flex justify-center">
          <img src={karnx} alt="karn" className="rounded-xl shadow-2xl" />
        </div>
      </div>
    </motion.div>
  );
};

// Features component
const Features = () => {
  return (
    <section className="py-24 bg-gradient-to-b from-gray-100 to-gray-200 dark:from-black dark:to-[#161717]">
      <div className="container mx-auto px-4">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-4xl font-bold text-center mb-16 text-gray-900 dark:text-gray-100"
        >
          Key Features
        </motion.h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {features.map((feature, index) => (
            <FeatureCard key={index} feature={feature} />
          ))}
        </div>

        <DownloadCard />
      </div>
    </section>
  );
};

export default Features;