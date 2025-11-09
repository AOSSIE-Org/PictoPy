import React, { useState } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import {
  FaHome,
  FaRobot,
  FaVideo,
  FaBookOpen,
  FaClock,
  FaCog,
} from "react-icons/fa";
import { motion } from "framer-motion";
import { useLocation, Link } from "react-router";
import { ROUTES } from "@/constants/routes";
import { Menu } from "lucide-react";

export function AppSidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const toggleSidebar = () => setCollapsed(!collapsed);

  const isActive = (path: string) => {
    const currentPath = location.pathname.replace(/^\//, "");
    const menuPath = path.replace(/^\//, "");

    if (menuPath === ROUTES.HOME || menuPath === "") {
      return currentPath === ROUTES.HOME || currentPath === "";
    }
    return currentPath === menuPath;
  };

  const menuItems = [
    { name: "Home", path: `/${ROUTES.HOME}`, icon: FaHome },
    { name: "AI Tagging", path: `/${ROUTES.AI}`, icon: FaRobot },
    { name: "Videos", path: `/${ROUTES.VIDEOS}`, icon: FaVideo },
    { name: "Albums", path: `/${ROUTES.ALBUMS}`, icon: FaBookOpen },
    { name: "Memories", path: `/${ROUTES.MEMORIES}`, icon: FaClock },
    { name: "Settings", path: `/${ROUTES.SETTINGS}`, icon: FaCog },
  ];

  return (
    <motion.div
      animate={{ width: collapsed ? 80 : 230 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="bg-background border-r border-border/30 shadow-md h-screen flex flex-col"
    >
      {/* Header */}
      <SidebarHeader className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        {!collapsed && (
          <div className="text-lg font-semibold tracking-wide text-foreground">
            PictoPy
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="text-muted-foreground hover:text-foreground transition"
          aria-label="Toggle sidebar"
        >
          <Menu size={22} />
        </button>
      </SidebarHeader>

      {/* Menu */}
      <SidebarContent className="flex-1 py-4 overflow-y-auto">
        <SidebarMenu className="space-y-1 px-2">
          {menuItems.map((item) => {
            const active = isActive(item.path);
            return (
              <SidebarMenuItem key={item.path}>
                <SidebarMenuButton
                  asChild
                  tooltip={item.name}
                  isActive={active}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-200 ${
                    active
                      ? "bg-primary/15 text-primary shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <Link to={item.path}>
                    <div className="flex items-center gap-3">
                      <item.icon className="h-5 w-5" />
                      {!collapsed && (
                        <span className="text-sm font-medium">
                          {item.name}
                        </span>
                      )}
                    </div>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter className="border-t border-border/30 py-4">
        {!collapsed && (
          <div className="text-muted-foreground space-y-1 px-4 text-xs">
            <div className="font-medium text-foreground/80">PictoPy v1.0.0</div>
            <div>© 2025 PictoPy</div>
          </div>
        )}
      </SidebarFooter>
    </motion.div>
  );
}
