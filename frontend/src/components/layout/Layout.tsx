import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Radar, FileText, Settings, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

const Sidebar = () => {
    const navItems = [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Scans', path: '/scans', icon: Radar },
        { name: 'Reports', path: '/reports', icon: FileText },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];

    return (
        <div className="flex h-screen w-64 flex-col bg-card border-r border-border">
            <div className="flex items-center gap-2 px-6 h-16 border-b border-border">
                <Activity className="h-6 w-6 text-primary" />
                <span className="font-bold text-lg tracking-tight">Market Intel Hub</span>
            </div>
            <nav className="flex-1 space-y-1 p-4">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            cn(
                                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-primary/10 text-primary"
                                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                            )
                        }
                    >
                        <item.icon className="h-4 w-4" />
                        {item.name}
                    </NavLink>
                ))}
            </nav>
            <div className="p-4 border-t border-border">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                        AD
                    </div>
                    <div className="text-xs">
                        <p className="font-medium text-foreground">Admin User</p>
                        <p className="text-muted-foreground">admin@example.com</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

const Layout = () => {
    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans antialiased">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
                <div className="container mx-auto p-6 max-w-7xl">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default Layout;
