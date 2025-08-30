import { FC, useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

const PictopyLogo = () => {
  const [logoError, setLogoError] = useState(false);
  
  return (
    <div className="h-20 w-20 md:h-24 md:w-24 rounded-2xl flex items-center justify-center overflow-hidden">
      {!logoError ? (
        <img 
          src="/PictoPy_Logo.png" 
          alt="PictoPy Logo" 
          className="w-full h-full object-contain"
          onError={() => setLogoError(true)}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-200 dark:bg-gray-700">
          <span className="text-gray-500 dark:text-gray-300 text-xs">Logo not found</span>
        </div>
      )}
    </div>
  );
};

const PictopyLanding: FC = () => {
  const [isVisible, setIsVisible] = useState(false);
  // Remove unused darkMode state, rely on Tailwind's dark class on <html>

  // Read dark mode from the HTML element (set by navbar)
  useEffect(() => {
    const checkDarkMode = () => {
  // Theme is controlled globally by Tailwind's dark class on <html>
  // No need to set local state, theme is controlled globally
    };

    // Initial check
    checkDarkMode();

    // Watch for changes to the dark class
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          checkDarkMode();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    return () => observer.disconnect();
  }, []);

  // Animate on mount
  useEffect(() => {
    setIsVisible(true);
  }, []);

  // Scroll to main Download button in Home1.tsx
  const scrollToMainDownload = () => {
    const btn = document.getElementById('main-download');
    if (btn) {
      const targetY = btn.getBoundingClientRect().top + window.scrollY - 180;
      window.scrollTo({ top: targetY, behavior: 'auto' });
    }
  };

  return (
    <section className="relative w-full py-16 md:py-32 min-h-screen bg-white dark:bg-black transition-all duration-300 overflow-hidden">

        {/* Enhanced Background Elements */}
        <div className="absolute inset-0 z-0">
          {/* Animated gradient orbs */}
          <div className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-r from-green-400 to-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-gradient-to-r from-yellow-400 to-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse delay-1000"></div>
          <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-gradient-to-r from-purple-400 to-green-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse delay-2000"></div>

          {/* Enhanced animated wave */}
          <svg
            className="absolute bottom-0 left-0 w-full h-64 md:h-80"
            viewBox="0 0 1440 320"
            xmlns="http://www.w3.org/2000/svg"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.1" />
                <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#eab308" stopOpacity="0.1" />
              </linearGradient>
            </defs>
            <path
              fill="url(#waveGradient)"
              d="M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
            >
              <animate
                attributeName="d"
                dur="8s"
                repeatCount="indefinite"
                values="
                  M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z;
                  M0,128L48,106.7C96,85,192,43,288,64C384,85,480,139,576,144C672,149,768,107,864,96C960,85,1056,107,1152,128C1248,149,1344,171,1392,192L1440,224V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z;
                  M0,192L48,160C96,128,192,64,288,58.7C384,53,480,107,576,128C672,149,768,128,864,101.3C960,75,1056,53,1152,69.3C1248,85,1344,139,1392,192L1440,256V320H1392C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
              />
            </path>
          </svg>

          {/* Floating particles */}
          <div className="absolute inset-0">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className={`absolute w-2 h-2 bg-green-400 rounded-full opacity-30 animate-float`}
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${i * 0.5}s`,
                  animationDuration: `${3 + Math.random() * 2}s`,
                }}
              />
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="container mx-auto px-4 md:px-6 relative z-10">
          <div className={`flex flex-col items-center text-center transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          } bg-white dark:bg-black`}>
            
            {/* Enhanced Logo and Title */}
            <div className="flex items-center justify-center gap-6 mb-8 group bg-white dark:bg-black rounded-2xl p-4">
              <div className="relative">
                <div className="absolute -inset-2 bg-gradient-to-r from-green-400 to-blue-500 rounded-full opacity-75 group-hover:opacity-100 blur-sm transition-opacity duration-300"></div>
                <div className="relative">
                  <PictopyLogo />
                </div>
              </div>
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-green-600 via-blue-600 to-yellow-500 transition-all duration-300 group-hover:from-yellow-500 group-hover:via-green-600 group-hover:to-blue-600 animate-gradient-x bg-300%">
                PictoPy
              </h1>
            </div>

            {/* Enhanced Subtitle */}
            <div className="mb-4">
              <p className="text-xl md:text-3xl lg:text-4xl font-medium text-gray-700 dark:text-gray-200 max-w-4xl mb-6 leading-relaxed bg-white dark:bg-black">
                Organize your photos effortlessly with{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-blue-600 font-bold">
                  AI-powered smart categorization
                </span>
              </p>
            </div>

            {/* Enhanced Download Buttons */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-8 bg-white dark:bg-black rounded-xl p-4">
              {/* Mac Button */}
              <Button
                className="group relative bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-900 hover:to-black text-white dark:text-white h-14 px-8 transition-all duration-300 border-2 border-transparent hover:border-gray-700 transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-gray-500/25 rounded-xl font-semibold text-lg overflow-hidden dark:bg-gradient-to-r dark:from-gray-800 dark:to-gray-900"
                size="lg"
                onClick={scrollToMainDownload}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
         <img 
           src="/mac.logo.png" 
           alt="Mac Logo" 
           className="w-7 h-7 relative z-10 rounded-lg object-contain transition-transform duration-300 group-hover:scale-110"
          />
                <span className="relative z-10 ml-3">Download for Mac</span>
              </Button>
              <Button
                className="group relative bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white dark:text-white h-14 px-8 transition-all duration-300 border-2 border-blue-400 hover:border-blue-300 transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-blue-500/25 rounded-xl font-semibold text-lg overflow-hidden scale-105 dark:bg-gradient-to-r dark:from-blue-500 dark:to-blue-600"
                size="lg"
                onClick={scrollToMainDownload}
              >
                <div className="absolute -top-1 -right-1 bg-gradient-to-r from-orange-400 to-red-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg animate-pulse">
                  Popular
                </div>
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
         <img 
           src="/windows.png" 
           alt="Windows Logo" 
           className="w-7 h-7 relative z-10 rounded-lg object-contain transition-transform duration-300 group-hover:scale-110"
          />
                <span className="relative z-10 ml-3">Download for Windows</span>
              </Button>

              {/* Linux Button */}
              <Button
                className="group relative bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white dark:text-white h-14 px-8 transition-all duration-300 border-2 border-transparent hover:border-yellow-400 transform hover:-translate-y-2 hover:shadow-2xl hover:shadow-yellow-500/25 rounded-xl font-semibold text-lg overflow-hidden dark:bg-gradient-to-r dark:from-yellow-500 dark:to-yellow-600"
                size="lg"
                onClick={scrollToMainDownload}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
                     <img
                      src="/Linux-logo.jpg"
                      alt="Linux Logo"
                      className="w-8 h-8 relative z-10 rounded-full object-contain bg-white p-1 shadow-md transition-transform duration-300 group-hover:scale-110 group-hover:shadow-lg"
                    />

                <span className="relative z-10 ml-3">Download for Linux(.deb)</span>
              </Button>
            </div>

            {/* Platform Support Info */}
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-gray-200/50 dark:border-gray-700/50 max-w-4xl">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Cross-Platform Compatibility</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
                PictoPy is designed for cross-platform compatibility. It's available on macOS, Linux and Windows, 
                allowing you to manage your photo collection seamlessly across all your devices with 
                synchronization options that respect your privacy preferences. Currently supporting Windows, Mac and Linux (Debian-based).
              </p>
            </div>

            {/* Additional Info - Simplified */}
            <p className="text-sm md:text-base text-gray-500 dark:text-gray-400 max-w-2xl bg-white dark:bg-black">
              No subscription required.
            </p>
          </div>
        </div>

        <style>{`
          @keyframes float {
            0%, 100% { 
              transform: translateY(0px) rotate(0deg); 
              opacity: 0.3;
            }
            50% { 
              transform: translateY(-20px) rotate(180deg); 
              opacity: 0.6;
            }
          }
          
          @keyframes gradient-x {
            0%, 100% {
              background-position: 0% 50%;
            }
            50% {
              background-position: 100% 50%;
            }
          }
          
          @keyframes slideInRight {
            from {
              opacity: 0;
              transform: translateX(100%);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }
          
          .animate-float {
            animation: float 3s ease-in-out infinite;
          }
          
          .animate-gradient-x {
            animation: gradient-x 3s ease infinite;
          }
          
          .animate-slideInRight {
            animation: slideInRight 0.3s ease-out;
          }
          
          .bg-300% {
            background-size: 300% 300%;
          }
        `}</style>
    </section>
  );
};

export default PictopyLanding;