import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import Sidebar from '@/components/Navigation/Sidebar/Sidebar';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex w-full flex-col">
      <Navbar />
      <div className="sidebar flex" style={{ height: 'calc(100vh - 64px)' }}>
        <Sidebar />
        <div className="flex flex-1 overflow-x-auto bg-white p-4 text-gray-900">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;
