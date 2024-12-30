import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import Sidebar from '@/components/Navigation/Sidebar/Sidebar';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex w-full flex-col">
      <Navbar title="User" />
      <div className="sidebar flex" style={{ height: 'calc(100vh - 92px)' }}>
        <div
          className="scrollbar-hide h-full overflow-y-auto"
          style={{ WebkitOverflowScrolling: 'touch' }}
        >
          <Sidebar />
        </div>
        <div className="flex flex-1 overflow-x-auto p-4">{children}</div>
      </div>
    </div>
  );
};

export default Layout;
