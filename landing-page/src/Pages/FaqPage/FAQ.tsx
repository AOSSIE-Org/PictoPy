// FAQ.tsx
import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Tag, Lock, Globe } from "lucide-react";

const faqs = [
  {
    question: "What is PictoPy?",
    answer:
      "PictoPy is an intelligent photo management application that uses advanced AI to automatically tag and organize your photos based on detected objects, faces, and scenes. It's designed to make your photo collection searchable and easily accessible while maintaining your privacy.",
    icon: <Tag className="w-5 h-5" />
  },
  {
    question: "How does the smart tagging feature work?",
    answer:
      "Our smart tagging system uses AI-powered object detection and facial recognition to analyze your photos. It automatically identifies people, objects, scenes, and activities in your images, creating searchable tags without requiring manual input. All processing happens on your device for maximum privacy.",
    icon: <Tag className="w-5 h-5" />
  },
  {
    question: "Is my privacy protected when using PictoPy?",
    answer:
      "Absolutely. PictoPy is built with a privacy-first approach. All image analysis and processing is performed locally on your device, and your photos never leave your control unless you explicitly choose to share them. We don't store or access your photos on our servers.",
    icon: <Lock className="w-5 h-5" />
  },
  {
    question: "What platforms does PictoPy support?",
    answer:
      "PictoPy is designed for cross-platform compatibility. It's available on iOS, Android, macOS, and Windows, allowing you to manage your photo collection seamlessly across all your devices with synchronization options that respect your privacy preferences.",
    icon: <Globe className="w-5 h-5" />
  }
];

export default function FAQ() {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [darkMode, ] = useState<boolean>(() => {
    return (
      localStorage.getItem("darkMode") === "true" ||
      (!("darkMode" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches)
    );
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("darkMode", darkMode.toString());
  }, [darkMode]);

  return (
    <section className="relative py-20 overflow-hidden min-h-screen transition-colors duration-300 bg-gray-50 text-black dark:bg-black dark:text-white">
      <BackgroundAnimation darkMode={darkMode} />
      
      <div className="container relative z-10 mx-auto px-4 md:px-8">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold py-2 mb-2 bg-clip-text text-transparent bg-gradient-to-r from-yellow-500 to-green-600 dark:from-yellow-400 dark:to-green-500">
            Frequently Asked Questions
          </h2>
          <p className="max-w-2xl mx-auto text-lg text-gray-600 dark:text-gray-300">
            Everything you need to know about PictoCopy's smart photo organization 
            and AI-powered tagging features.
          </p>
        </motion.div>

        <div className="max-w-3xl mx-auto space-y-6">
          {faqs.map((faq, index) => (
            <FAQItem
              key={index}
              question={faq.question}
              answer={faq.answer}
              isOpen={activeIndex === index}
              onClick={() => setActiveIndex(activeIndex === index ? null : index)}
              index={index}
              icon={faq.icon}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

interface FAQItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
  index: number;
  icon: React.ReactNode;
}

function FAQItem({ question, answer, isOpen, onClick, index, icon }: FAQItemProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  return (
    <motion.div
      className="rounded-xl overflow-hidden transition-all duration-300 
        bg-white dark:bg-black border border-gray-100 dark:border-gray-800 
        hover:shadow-md dark:hover:shadow-green-900/10"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      viewport={{ once: true }}
    >
      <button
        className="flex justify-between items-center w-full text-left p-6 group"
        onClick={onClick}
        aria-expanded={isOpen}
      >
        <div className="flex items-center">
          <div className={`mr-4 p-2 rounded-full 
            ${isOpen ? 'bg-green-100 text-green-600 dark:bg-green-900/50 dark:text-green-300' : 
            'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400 group-hover:bg-green-50 group-hover:text-green-500 dark:group-hover:bg-green-900/30 dark:group-hover:text-green-300'} 
            transition-colors duration-300`}>
            {icon}
          </div>
          <span className="font-semibold text-lg">{question}</span>
        </div>
        <div className={`p-1 rounded-full transition-colors duration-300
          ${isOpen ? 'bg-green-100 text-green-600 dark:bg-green-900/50 dark:text-green-300' : 
          'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400 group-hover:bg-green-50 group-hover:text-green-500 dark:group-hover:bg-green-900/30 dark:group-hover:text-green-300'}`}>
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: contentRef.current?.scrollHeight || "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div ref={contentRef} className="px-6 pb-6 pl-16 text-gray-600 dark:text-gray-300 leading-relaxed">
              <p>{answer}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function BackgroundAnimation({ darkMode }: { darkMode: boolean }) {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Fixed dots pattern */}
      <div className="absolute inset-0" style={{ 
        backgroundImage: `radial-gradient(${darkMode ? '#4B5563' : '#e5e7eb'} 1px, transparent 0)`,
        backgroundSize: '30px 30px',
        opacity: 0.4
      }}></div>
      {/* Animated SVG elements */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute"
          initial={{ opacity: 0.2, scale: 0.8, x: "10%", y: "10%" }}
          animate={{ 
            opacity: [0.2, 0.3, 0.2],
            scale: [0.8, 1, 0.8],
            x: ["10%", "15%", "10%"],
            y: ["10%", "5%", "10%"]
          }}
          transition={{ 
            repeat: Infinity,
            duration: 20,
            ease: "easeInOut" 
          }}
        >
          <svg width="400" height="400" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M50 5 L95 50 L50 95 L5 50 Z" fillOpacity="0.05" stroke={darkMode ? "#84cc16" : "#65a30d"} strokeWidth="0.5" />
          </svg>
        </motion.div>
      </div>
    </div>
  );
}
