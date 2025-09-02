import type React from "react"
import { FaDiscord } from 'react-icons/fa'  // Import Discord icon from React Icons

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
              <FaDiscord className="inline-block mr-2 text-yellow-400 hover:text-green-400 transition duration-300 ease-in-out transform scale-150" /> {/* Scale it to 1.5x */}
              <span>Made with love by AOSSIE team</span>
            </a>
          </div>
        </div>

        <div className="mt-4 text-center border-t border-white pt-2">
          {/* You can add any content here if needed */}
        </div>
      </div>
    </footer>
  )
}

export default Footer
