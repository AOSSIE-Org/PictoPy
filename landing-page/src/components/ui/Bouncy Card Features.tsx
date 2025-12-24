import { ReactNode } from "react"; // Removed unused React import
import { motion } from "motion/react"
import { 
  Images, 
  
  Scissors, 
  
  Microscope, 
  Settings 
} from "lucide-react";

export const BouncyCardsFeatures = () => {
  const features = [
    {
      title: "Image Gallery Management",
      description: "Organize, view, and categorize your images effortlessly.",
      icon: <Images className="w-12 h-12 text-indigo-500" />,
      gradient: "from-violet-400 to-indigo-400 dark:from-indigo-900 dark:to-indigo-800"
    },
    {
      title: "Advanced Image Analysis",
      description: "Perform sophisticated analysis using Python's powerful libraries.",
      icon: <Microscope className="w-12 h-12 text-orange-500" />,
      gradient: "from-amber-400 to-orange-400 dark:from-orange-800 dark:to-amber-700"
    },
    {
      title: "Dynamic Image Processing",
      description: "Edit and process images in real-time with advanced tools.",
      icon: <Scissors className="w-12 h-12 text-green-500" />,
      gradient: "from-green-400 to-emerald-400 dark:from-emerald-800 dark:to-green-700"
    },
    {
      title: "Customizable Interface",
      description: "Tailor the interface to fit your workflow.",
      icon: <Settings className="w-12 h-12 text-pink-500" />,
      gradient: "from-pink-400 to-red-400 dark:from-red-800 dark:to-pink-700"
    }
  ];

  return (
    <section className="mx-auto max-w-7xl px-4 py-12 text-slate-800 dark:text-slate-200">
      <motion.div 
        className="mb-12 text-center"
        initial={{ opacity: 0, y: -50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 1 }}
      >
        <h2 className="text-4xl md:text-5xl font-bold mb-4">
          Supercharge Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-500 to-green-500">Image Workflow</span>
        </h2>
        <p className="max-w-2xl mx-auto text-xl text-slate-600 dark:text-slate-400">
          PictoPy brings intelligent image management and analysis to your fingertips
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            whileInView={{ opacity: 1, y: 0 }}
            initial={{ opacity: 0, y: 50 }}
            transition={{ delay: index * 0.2, duration: 0.75 }}
            viewport={{ once: true }}
          >
            <BounceCard>
              <div className="flex flex-col h-full">
                <div className="flex items-center mb-4">
                  {feature.icon}
                  <CardTitle className="ml-4">{feature.title}</CardTitle>
                </div>
                <div 
                  className={`absolute bottom-0 left-4 right-4 top-32 translate-y-8 
                    rounded-t-2xl bg-gradient-to-br ${feature.gradient} 
                    p-4 transition-transform duration-[250ms] 
                    group-hover:translate-y-4 group-hover:rotate-[2deg]`}
                >
                  <span className="block text-center font-semibold text-white">
                    {feature.description}
                  </span>
                </div>
              </div>
            </BounceCard>
          </motion.div>
        ))}
      </div>
    </section>
  );
};

interface BounceCardProps {
  className?: string;
  children: ReactNode;
}

const BounceCard = ({ className, children }: BounceCardProps) => {
  return (
    <motion.div
      whileHover={{ scale: 1.05, rotate: "-2deg" }}
      className={`group relative min-h-[300px] cursor-pointer 
        overflow-hidden rounded-2xl 
        bg-white dark:bg-[#1a1a1a] 
        shadow-xl hover:shadow-2xl 
        transition-all duration-300 
        border border-slate-100 dark:border-slate-800 
        p-6 ${className}`}
    >
      {children}
    </motion.div>
  );
};

interface CardTitleProps {
  children: ReactNode;
  className?: string;
}

const CardTitle = ({ children, className }: CardTitleProps) => {
  return (
    <motion.h3
      className={`text-2xl font-bold dark:text-slate-100 ${className}`}
      whileInView={{ y: 0 }}
      initial={{ y: 20 }}
      transition={{ duration: 0.5 }}
    >
      {children}
    </motion.h3>
  );
};

export default BouncyCardsFeatures;