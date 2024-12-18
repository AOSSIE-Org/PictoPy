import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import Sidebar from '@/components/Navigation/Sidebar/Sidebar';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex w-full flex-col bg-gray-900">
      <div className="sidebar flex" style={{ height: '100vh' }}>
        <Sidebar />
        <div className="flex flex-1 overflow-x-auto p-4 text-white">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;
