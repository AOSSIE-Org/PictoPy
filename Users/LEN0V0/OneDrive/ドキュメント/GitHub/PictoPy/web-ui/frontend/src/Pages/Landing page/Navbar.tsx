import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import YourLogo from "@/assets/38881995.png"; // Update this import path to your logo

interface NavLinkProps {
  to: string;
  children: React.ReactNode;
  onClick?: () => void;
  isScrollLink?: boolean;
}

const NavLink: React.FC<NavLinkProps> = ({
  to,
  children,
  onClick,
  isScrollLink = false,
}) => {
  // Handle scroll to section
  const handleClick = (e: React.MouseEvent) => {
    if (isScrollLink) {
      e.preventDefault();

      // Remove the # from the target
      const targetId = to.replace("#", "");
      const element = document.getElementById(targetId);

      if (element) {
        // Scroll to the element with smooth behavior
        element.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }

      // Call additional onClick handler if provided
      if (onClick) onClick();
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <Link
      to={to}
      onClick={handleClick}
      className="text-gray-300 text-lg font-medium 
      hover:text-white 
      relative after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0
      after:bg-gradient-to-r after:from-yellow-500 after:to-green-500
      hover:after:w-full after:transition-all after:duration-300
      transition duration-300"
    >
      {children}
    </Link>
  );
};

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [isClient, setIsClient] = useState(false);

  // Ensure we're on client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Force dark mode on component mount and keep it
  useEffect(() => {
    if (!isClient) return;

    const applyDarkMode = () => {
      try {
        const html = document.documentElement;
        const body = document.body;

        // Force dark mode classes
        html.classList.add("dark");
        html.setAttribute("data-theme", "dark");
        body.classList.add("dark");

        // Set color scheme for mobile browsers
        html.style.colorScheme = "dark";
        
        // Force background color change for mobile
        body.style.backgroundColor = "#000000";
        body.style.color = "#ffffff";
        html.style.backgroundColor = "#000000";
        
        // Force theme-color meta update for mobile browsers
        const themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (themeColorMeta) {
          themeColorMeta.setAttribute('content', '#000000');
        } else {
          // Create theme-color meta if it doesn't exist
          const meta = document.createElement('meta');
          meta.name = 'theme-color';
          meta.content = '#000000';
          document.head.appendChild(meta);
        }

        // Save dark mode to localStorage
        if (typeof Storage !== 'undefined' && window.localStorage) {
          try {
            localStorage.setItem("darkMode", "true");
          } catch (e) {
            console.warn("Cannot save to localStorage:", e);
          }
        }

        // Mobile repaint logic
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (isMobile) {
          const forceRepaint = () => {
            html.style.transform = 'translateZ(0)';
            html.style.backfaceVisibility = 'hidden';
            
            requestAnimationFrame(() => {
              html.style.transform = '';
              html.style.backfaceVisibility = '';
              
              const originalDisplay = html.style.display;
              html.style.display = 'none';
              html.offsetHeight; // Force reflow
              html.style.display = originalDisplay;
            });
          };

          forceRepaint();
          setTimeout(forceRepaint, 100);
        }

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { 
          detail: { darkMode: true } 
        }));

      } catch (error) {
        console.error("Error applying dark mode:", error);
      }
    };

    // Apply dark mode immediately
    applyDarkMode();
  }, [isClient]);

  // Handle scroll to adjust navbar styles
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Add viewport meta tag check for mobile
  useEffect(() => {
    const viewport = document.querySelector('meta[name="viewport"]');
    if (!viewport) {
      const meta = document.createElement('meta');
      meta.name = 'viewport';
      meta.content = 'width=device-width, initial-scale=1.0, user-scalable=yes';
      document.getElementsByTagName('head')[0].appendChild(meta);
    }
  }, []);

  return (
    <>
      <nav
        className={`fixed top-4 left-1/2 -translate-x-1/2 w-[95%] max-w-6xl z-50 
        transition-all duration-300 ease-in-out 
        bg-black/50 backdrop-blur-md 
        rounded-3xl overflow-hidden
        ${scrolled ? "shadow-lg shadow-black/40" : "shadow-none"}
        ${scrolled ? "w-[90%]" : "w-[95%]"}`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex-shrink-0 flex items-center">
              <div className="mr-4">
                <Link to="/">
                  <img
                    src={YourLogo}
                    alt="PictoPy Logo"
                    className="w-10 h-10 object-contain"
                  />
                </Link>
              </div>

              {/* Tooltip on hover */}
              <div className="relative group">
                <Link
                  to="/"
                  className="text-2xl font-bold 
                  bg-gradient-to-r from-yellow-500 to-green-500 
                  bg-clip-text text-transparent
                  hover:from-green-600 hover:to-yellow-600 
                  transition-colors duration-300"
                >
                  PictoPy
                </Link>

                {/* Custom Tooltip with Gradient */}
                <div
                  className="absolute left-1/2 transform -translate-x-1/2 bottom-12 hidden group-hover:block 
                  bg-gradient-to-r from-yellow-500 to-green-500 text-white text-sm px-2 py-1 rounded-md shadow-md"
                >
                  Ready to sort images
                </div>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <NavLink to="/">Home</NavLink>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center">
              {/* Mobile Menu Toggle */}
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-3 rounded-full text-gray-300 
                hover:text-white
                bg-black/80 backdrop-blur-sm
                hover:bg-gray-800
                border border-gray-700
                shadow-sm hover:shadow-md
                transition-all duration-300 touch-manipulation
                active:scale-95"
                type="button"
                aria-label="Toggle menu"
                style={{ 
                  WebkitTapHighlightColor: 'transparent',
                  minWidth: '48px',
                  minHeight: '48px'
                }}
              >
                {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div
          className={`md:hidden fixed inset-0 z-50 
          bg-black
          transform transition-transform duration-300 ease-in-out 
          ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <div className="pt-16 pb-6 px-4 space-y-6">
            <div className="space-y-4 flex flex-col items-start">
              <NavLink to="/" onClick={() => setIsOpen(false)}>
                Home
              </NavLink>
              <NavLink to="#features" isScrollLink={true} onClick={() => setIsOpen(false)}>
                Feature
              </NavLink>
              <NavLink to="#about" isScrollLink={true} onClick={() => setIsOpen(false)}>
                About
              </NavLink>

              <Button
                className="w-full bg-black 
                text-white 
                hover:bg-green-700 
                transition-colors duration-300 mt-4"
                onClick={() => setIsOpen(false)}
              >
                Download
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Overlay for mobile menu */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Navbar;