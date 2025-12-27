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
        // Scroll with offset to account for sticky navbar
        const offset = 90;
        const elementTop = element.getBoundingClientRect().top + window.scrollY;
        const targetScroll = elementTop - offset;

        window.scrollTo({
          top: targetScroll,
          behavior: "smooth",
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
      className="text-gray-700 dark:text-gray-300 text-lg font-medium 
      hover:text-black dark:hover:text-white 
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
  const [darkMode, setDarkMode] = useState<boolean>(false);

  // Load dark mode setting from localStorage or fallback to system preference
  useEffect(() => {
    const savedDarkMode = localStorage.getItem("darkMode");

    if (savedDarkMode !== null) {
      setDarkMode(savedDarkMode === "true");
    } else {
      const prefersDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setDarkMode(prefersDarkMode);
    }
  }, []);

  // Apply dark mode class to body when darkMode state changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("darkMode", "true");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("darkMode", "false");
    }
  }, [darkMode]);

  // Handle scroll to adjust navbar styles
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll);

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <nav
        className={`fixed top-4 left-1/2 -translate-x-1/2 w-[95%] max-w-6xl z-50 
        transition-all duration-300 ease-in-out 
        bg-white/70 dark:bg-black/50 backdrop-blur-md 
        rounded-3xl overflow-hidden
        ${scrolled ? "shadow-lg shadow-gray-300/50 dark:shadow-black/40" : "shadow-none"}
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
              <NavLink to="#home" isScrollLink={true}>Home</NavLink>

              {/* Dark Mode Toggle Button */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="text-gray-800 dark:text-gray-300 
                hover:text-black dark:hover:text-white 
                transition-colors duration-300"
              >
                <span className="sr-only">Toggle dark mode</span>
                {darkMode ? <span>🌙</span> : <span>🌞</span>}
              </button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center space-x-4">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="text-gray-800 dark:text-gray-300 
                hover:text-black dark:hover:text-white 
                transition-colors duration-300"
              >
                <span className="sr-only">Toggle dark mode</span>
                {darkMode ? <span>🌙</span> : <span>🌞</span>}
              </button>
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="text-gray-800 dark:text-gray-300 
                hover:text-black dark:hover:text-white 
                transition-colors duration-300"
              >
                <span className="sr-only">Open menu</span>
                {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div
          className={`md:hidden fixed inset-0 z-50 
          bg-white dark:bg-black
          transform transition-transform duration-300 ease-in-out 
          ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <div className="pt-16 pb-6 px-4 space-y-6">
            <div className="space-y-4 flex flex-col items-start">
              <NavLink to="#home" isScrollLink={true} onClick={() => setIsOpen(false)}>
                Home
              </NavLink>
              <NavLink to="#features" isScrollLink={true} onClick={() => setIsOpen(false)}>
                Feature
              </NavLink>
              <NavLink to="#about" isScrollLink={true} onClick={() => setIsOpen(false)}>
                About
              </NavLink>
              <Button
                className="w-full bg-gray-800 dark:bg-black 
                text-white 
                hover:bg-green-700 dark:hover:bg-green-800 
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
