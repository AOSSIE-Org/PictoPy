import type React from "react"
import { FaDiscord, FaGithub, FaEnvelope, FaTwitter, FaLinkedin } from 'react-icons/fa'

const Footer: React.FC = () => {
  return (
    <footer className="relative bg-black text-white py-8 overflow-hidden">
      <div className="relative container mx-auto px-6">
        <div className="flex justify-between items-center">
          {/* Left-aligned PictoPy text */}
          <div className="flex items-center space-x-2">
            <p className="text-xl font-medium text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400 hover:scale-105 transition-all duration-300 ease-in-out">
              PictoPy
            </p>
          </div>

          {/* Right-aligned Discord Icon and "Made with love" text */}
          <div className="flex items-center space-x-2">
            <a 
              href="https://discord.com/channels/1022871757289422898/1311271974630330388" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-sm font-medium text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400 hover:bg-gradient-to-r hover:from-yellow-500 hover:to-green-500 transition duration-300 ease-in-out"
            >
              <FaDiscord className="inline-block mr-2 text-yellow-400 hover:text-green-400 transition duration-300 ease-in-out transform scale-150" />
              <span>Made with love by AOSSIE team</span>
            </a>
          </div>
        </div>

        <div className="mt-8 border-t border-gray-700 pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-6">
            {/* About Section - Left */}
            <div className="text-left">
              <h3 className="text-lg font-semibold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400">
                About PictoPy
              </h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                An innovative image processing library designed to make computer vision accessible and powerful for developers.
              </p>
            </div>

            {/* Quick Links Section - Center */}
            <div className="text-center md:text-center">
              <h3 className="text-lg font-semibold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400">
                Quick Links
              </h3>
              <ul className="space-y-2 inline-block text-left">
                <li>
                  <a 
                    href="https://github.com/AOSSIE-Org/PictoPy" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 text-sm flex items-center"
                  >
                    <FaGithub className="mr-2" /> GitHub Repository
                  </a>
                </li>
                <li>
                  <a 
                    href="https://github.com/AOSSIE-Org/PictoPy/blob/main/README.md" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 text-sm flex items-center"
                  >
                    <FaGithub className="mr-2" /> Documentation
                  </a>
                </li>
                <li>
                  <a 
                    href="https://github.com/AOSSIE-Org/PictoPy/blob/main/CONTRIBUTING.md" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 text-sm flex items-center"
                  >
                    <FaGithub className="mr-2" /> Contributing Guide
                  </a>
                </li>
              </ul>
            </div>

            {/* Contact & Social Section - Right */}
            <div className="text-right md:text-right">
              <h3 className="text-lg font-semibold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-green-400">
                Connect With Us
              </h3>
              <div className="space-y-3">
                <a 
                  href="mailto:aossie.oss@gmail.com" 
                  className="text-gray-400 hover:text-yellow-400 transition duration-300 text-sm flex items-center justify-end"
                >
                  <FaEnvelope className="mr-2" /> aossie.oss@gmail.com
                </a>
                <div className="flex space-x-4 mt-4 justify-end">
                  <a 
                    href="https://github.com/AOSSIE-Org" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 transform hover:scale-110"
                    aria-label="GitHub"
                  >
                    <FaGithub size={24} />
                  </a>
                  <a 
                    href="https://discord.com/channels/1022871757289422898/1311271974630330388" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 transform hover:scale-110"
                    aria-label="Discord"
                  >
                    <FaDiscord size={24} />
                  </a>
                  <a 
                    href="https://twitter.com/aossie_org" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 transform hover:scale-110"
                    aria-label="Twitter"
                  >
                    <FaTwitter size={24} />
                  </a>
                  <a 
                    href="https://www.linkedin.com/company/aossie" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-yellow-400 transition duration-300 transform hover:scale-110"
                    aria-label="LinkedIn"
                  >
                    <FaLinkedin size={24} />
                  </a>
                </div>
              </div>
            </div>
          </div>

          
        </div>
      </div>
    </footer>
  )
}

export default Footer
