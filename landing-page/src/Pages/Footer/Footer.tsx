import type React from "react"
import { FaDiscord } from 'react-icons/fa'  // Import Discord icon from React Icons

const Footer: React.FC = () => {
  return (
    <footer className="relative bg-white dark:bg-black text-gray-900 dark:text-white py-8 overflow-hidden transition-colors duration-300 border-t border-gray-100 dark:border-gray-900">
      <div className="relative container mx-auto px-6">
        <div className="flex justify-between items-center">
          {/* Left-aligned PictoPy text */}
          <div className="flex items-center space-x-2">
            <p className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-500 to-green-500 hover:scale-105 transition-all duration-300 ease-in-out">
              PictoPy
            </p>
          </div>

          {/* Right-aligned Discord Icon and "Made with love" text */}
          <div className="flex items-center space-x-2">
            <a 
              href="https://discord.com/channels/1022871757289422898/1311271974630330388" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-sm font-medium hover:opacity-80 transition duration-300 ease-in-out flex items-center"
            >
              <FaDiscord className="mr-2 text-yellow-500 hover:text-green-500 transition duration-300 ease-in-out transform scale-150" />
              <span className="bg-gradient-to-r from-yellow-600 to-green-600 dark:from-yellow-400 dark:to-green-400 bg-clip-text text-transparent">Made with love by AOSSIE team</span>
            </a>
          </div>
        </div>

        <div className="mt-4 text-center border-t border-gray-100 dark:border-gray-900 pt-2">
          {/* You can add any content here if needed */}
        </div>
      </div>
    </footer>
  )
}

export default Footer
