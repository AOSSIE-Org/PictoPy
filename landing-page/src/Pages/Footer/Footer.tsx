import React from 'react';
import { FaDiscord, FaGithub, FaTwitter } from 'react-icons/fa';
import { MdEmail } from 'react-icons/md';

const Footer = () => {
  return (
    <footer className="relative bg-black text-white py-8 overflow-hidden">
      <div className="relative container mx-auto px-6">
        {/* Main Content */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          
          {/* Left Section - Branding */}
          <div className="flex flex-col items-center md:items-start space-y-2">
            <p className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400 hover:scale-105 transition-all duration-300 ease-in-out cursor-default">
              PictoPy
            </p>
            <p className="text-sm text-gray-400">
              Transforming images with Python
            </p>
          </div>

          {/* Center Section - Quick Links */}
          <div className="flex flex-col items-center space-y-2">
            <h3 className="text-sm font-semibold text-gray-300 mb-1">Connect With Us</h3>
            <div className="flex items-center space-x-4">
              <a 
                href="https://discord.com/channels/1022871757289422898/1311271974630330388" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-yellow-400 transition-all duration-300 transform hover:scale-110"
                aria-label="Join our Discord"
              >
                <FaDiscord size={24} />
              </a>
              
              <a 
                href="https://github.com/AOSSIE-Org" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-green-400 transition-all duration-300 transform hover:scale-110"
                aria-label="Visit our GitHub"
              >
                <FaGithub size={24} />
              </a>
              
              <a 
                href="https://twitter.com/aossie_org" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-blue-400 transition-all duration-300 transform hover:scale-110"
                aria-label="Follow us on Twitter"
              >
                <FaTwitter size={24} />
              </a>
              
              <a 
                href="mailto:contact@aossie.org" 
                className="text-gray-400 hover:text-red-400 transition-all duration-300 transform hover:scale-110"
                aria-label="Email us"
              >
                <MdEmail size={24} />
              </a>
            </div>
          </div>

          {/* Right Section - Credits */}
          <div className="flex flex-col items-center md:items-end space-y-2">
            <a 
              href="https://discord.com/channels/1022871757289422898/1311271974630330388" 
              target="_blank" 
              rel="noopener noreferrer"
              className="group flex items-center space-x-2"
            >
              <span className="text-sm font-medium text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400 group-hover:from-yellow-500 group-hover:to-green-500 transition-all duration-300">
                Made with ❤️ by AOSSIE team
              </span>
            </a>
          </div>
        </div>

        {/* Bottom Section - Copyright */}
        <div className="mt-8 pt-6 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-500">
            <p>© {new Date().getFullYear()} PictoPy. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;