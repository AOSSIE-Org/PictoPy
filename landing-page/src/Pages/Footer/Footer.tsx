import { Link } from "react-router-dom";
import { FaDiscord, FaGithub, FaBook, FaHandsHelping } from "react-icons/fa";

const Footer = () => {
  return (
    <footer
      className="bg-black text-white border-t border-white/10"
      aria-label="Footer"
    >
      <div className="container mx-auto px-6 py-10">
        {/* Main Footer Content */}
        <div className="flex flex-col md:flex-row justify-between gap-8">
          
          {/* Project Info */}
          <div className="space-y-2 max-w-sm">
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
            <p className="text-sm text-gray-400">
              AI-powered, privacy-first photo management application with smart
              tagging and local-first processing.
            </p>
          </div>

          {/* Resources */}
          <div className="space-y-2">
            <p className="text-sm font-semibold text-gray-300">Resources</p>
            <ul className="space-y-1 text-sm text-gray-400">
              <li>
                <a
                  href="https://github.com/AOSSIE-Org/PictoPy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 hover:text-green-400 transition"
                >
                  <FaGithub />
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://aossie-org.github.io/PictoPy/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 hover:text-green-400 transition"
                >
                  <FaBook />
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/AOSSIE-Org/PictoPy/blob/main/CONTRIBUTING.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 hover:text-green-400 transition"
                >
                  <FaHandsHelping />
                  Contribute
                </a>
              </li>
            </ul>
          </div>

          {/* Community */}
          <div className="space-y-2">
            <p className="text-sm font-semibold text-gray-300">Community</p>
            <a
              href="https://discord.com/channels/1022871757289422898/1311271974630330388"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Join PictoPy Discord community"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-green-400 transition"
            >
              <FaDiscord className="text-lg" />
              Join our Discord
            </a>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-4 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-gray-500">
          <span>
            © {new Date().getFullYear()} PictoPy · An open-source project by AOSSIE
          </span>
          <span className="flex items-center gap-1">
            Made with <span className="text-red-500">❤️</span> by AOSSIE team
          </span>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
