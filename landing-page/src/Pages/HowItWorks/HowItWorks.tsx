import { motion } from "motion/react"
import { useState } from "react";

const steps = [
  {
    title: "Smart Tagging",
    description: "Automatically tag photos based on detected objects and faces.",
    details:
      "Our advanced image analysis uses object detection and facial recognition to automatically tag your photos, making organization effortless.",
    icon: "🏷️"
  },
  {
    title: "Album Management",
    description: "Organize your photos into albums with ease.",
    details: "Create, edit, and manage albums to keep your photos organized and easily accessible.",
    icon: "📁"
  },
  {
    title: "Advanced Image Analysis",
    description: "Detect objects and recognize faces in your photos.",
    details:
      "Leverage cutting-edge technology to analyze your photos, detect objects, and recognize faces for better organization and searchability.",
    icon: "🔍"
  },
  {
    title: "Privacy & Offline Access",
    description: "Enjoy a privacy-focused design with offline functionality.",
    details:
      "Your data stays on your device. Our app works offline, ensuring your privacy and allowing you to access your gallery anytime, anywhere.",
    icon: "🔒"
  }
];

export default function GalleryFeatures() {
  const [activeStep, setActiveStep] = useState<number | null>(null);

  return (
    <section className="py-20 bg-gray-50 dark:bg-black transition-colors duration-300">
      <div className="container mx-auto px-4">
        <h2 className="text-4xl font-bold text-center mb-12 text-gray-900 dark:text-white">
          Gallery Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }} 
              whileHover={{ y: -5 }}
            >
              <div 
                className={`bg-white dark:bg-[#121212]  /* Off-Black Card */
                  rounded-xl border border-gray-200 dark:border-gray-800
                  shadow-md hover:shadow-lg 
                  p-6 cursor-pointer h-full  /* Change cursor to pointer on hover */
                  transition-all duration-300 
                  relative
                  ${activeStep === index ? 'ring-2 ring-pink-500 dark:ring-pink-400' : ''}`}
                onClick={() => setActiveStep(activeStep === index ? null : index)}
                style={{
                  cursor: `url('data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Ctext x="10" y="40" font-size="40"%3E${encodeURIComponent(step.icon)}%3C/text%3E%3C/svg%3E'), auto`
                }}
              >
                {/* Step Number Badge */}
                <div className="absolute -top-4 left-4 bg-gradient-to-br from-yellow-500 to-green-600 dark:from-green-400 dark:to-yellow-500 text-white rounded-full w-10 h-10 flex items-center justify-center shadow-lg">
                  {index + 1}
                </div>
                
                {/* Step Icon */}
                <div className="absolute -top-4 right-4 text-2xl">
                  {step.icon}
                </div>

                <div className="pt-4">
                  <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 mb-4">
                    {step.description}
                  </p>

                  {/* Expandable Step Details */}
                  {activeStep === index && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4"
                    >
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {step.details}
                      </p>
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
