import { Navbar } from "@/components/Navigation/Navbar/Navbar";
import Sidebar from "@/components/Navigation/Sidebar/Sidebar";

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex flex-col w-full">
      <Navbar />
      <div className="flex sidebar" style={{ height: "calc(100vh - 64px)" }}>
        <Sidebar />
        <div className="flex flex-1 bg-gray-900 text-white p-4 overflow-x-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;
