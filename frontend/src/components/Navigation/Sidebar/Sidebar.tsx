import {
  AlbumIcon,
  FileIcon,
  HomeIcon,
  ImageIcon,
  SettingsIcon,
  VideoIcon,
} from "@/components/Icons/Icons";
import { Link, useLocation } from "react-router-dom";

function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const linkClasses = (path: string) =>
    `flex items-center flex-col gap-2 ${
      isActive(path)
        ? "text-[#6465F3] glow"
        : "text-white hover:text-gray-50 dark:text-gray-400 dark:hover:text-gray-50"
    }`;

  return (
    <div className="flex sidebar flex-col justify-between bg-[#333333] w-40 border-r border-gray-700 dark:border-gray-700 p-4 space-y-4">
      <div className="flex flex-col mt-2 gap-10">
        <Link to="/home" className={linkClasses("/home")}>
          <HomeIcon
            className="h-5 w-5"
            fillColor={isActive("/home") ? "#6465F3" : "  none"}
          />
          <span className="font-sans">Home</span>
        </Link>
        <Link to="/ai-tagging" className={linkClasses("/ai-tagging")}>
          <FileIcon
            className="h-5 w-5"
            fillColor={isActive("/ai-tagging") ? "#6465F3" : "none"}
          />
          <span className="font-sans">Ai tagging</span>
        </Link>
        <Link to="/photos" className={linkClasses("/photos")}>
          <ImageIcon
            className="h-5 w-5"
            fillColor={isActive("/photos") ? "#6465F3" : "none"}
          />
          <span className="font-sans">Photos</span>
        </Link>
        <Link to="/videos" className={linkClasses("/videos")}>
          <VideoIcon
            className="h-5 w-5"
            fillColor={isActive("/videos") ? "#6465F3" : "currentColor"}
          />
          <span className="font-sans">Videos</span>
        </Link>
        <Link to="/albums" className={linkClasses("/albums")}>
          <AlbumIcon
            className="h-5 w-5"
            fillColor={isActive("/albums") ? "#6465F3" : "  none"}
          />
          <span className="font-sans">Albums</span>
        </Link>
      </div>
      <Link to="/settings" className={linkClasses("/settings")}>
        <SettingsIcon
          fillColor={isActive("/settings") ? "#6465F3" : "currentColor"}
        />
        <span className="font-sans">Settings</span>
      </Link>
    </div>
  );
}

export default Sidebar;
