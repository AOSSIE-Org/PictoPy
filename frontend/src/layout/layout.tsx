import { Navbar } from '@/components/Navigation/Navbar/Navbar';
import { AppSidebar } from '@/components/Navigation/Sidebar/AppSidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Outlet } from 'react-router';
const Layout: React.FC = () => {
  return (
    <SidebarProvider>
      <div className="flex w-full flex-col">
        <Navbar />
        <div className="flex" style={{ height: 'calc(100vh - 56px)' }}>
          <AppSidebar />
          <div className="w-full overflow-y-auto p-4">
            <Outlet />
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Layout;
