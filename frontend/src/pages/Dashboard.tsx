import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Activity, AlertTriangle, FileText } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts';

// Realistic dummy pricing trends for December 2025
const data = [
    { name: 'Dec 1', vercel: 20, netlify: 19, cloudflare: 25 },
    { name: 'Dec 5', vercel: 20, netlify: 19, cloudflare: 25 },
    { name: 'Dec 10', vercel: 20, netlify: 19, cloudflare: 24 },
    { name: 'Dec 15', vercel: 20, netlify: 15, cloudflare: 25 }, // Netlify drops price
    { name: 'Dec 18', vercel: 20, netlify: 15, cloudflare: 25 },
    { name: 'Dec 22', vercel: 24, netlify: 15, cloudflare: 25 }, // Vercel increases price
    { name: 'Dec 25', vercel: 24, netlify: 15, cloudflare: 25 },
    { name: 'Dec 28', vercel: 24, netlify: 19, cloudflare: 25 }, // Netlify restores price
    { name: 'Dec 31', vercel: 24, netlify: 19, cloudflare: 25 },
];

const Dashboard = () => {
    // Fetch system health (mocked for now)
    const { data: health, isLoading } = useQuery({
        queryKey: ['health'],
        queryFn: async () => {
            return { status: 'healthy', active_agents: 3, uptime: '48h' };
        },
    });

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="px-3 py-1">System Status: {isLoading ? 'Checking...' : health?.status}</Badge>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card className="border-l-4 border-l-primary bg-gradient-to-br from-card/80 to-secondary/20 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Monitoring Targets</CardTitle>
                        <Activity className="h-4 w-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">3</div>
                        <p className="text-xs text-muted-foreground">Vercel, Netlify, Cloudflare</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-destructive bg-gradient-to-br from-card/80 to-secondary/20 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Critical Changes</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-destructive" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">2</div>
                        <p className="text-xs text-muted-foreground">Pricing shifts detected recently</p>
                    </CardContent>
                </Card>

                <Card className="border-l-4 border-l-secondary bg-gradient-to-br from-card/80 to-secondary/20 backdrop-blur">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Reports Generated</CardTitle>
                        <FileText className="h-4 w-4 text-secondary-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">12</div>
                        <p className="text-xs text-muted-foreground">Last 30 Days</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Main Chart */}
                <Card className="col-span-4 bg-gradient-to-br from-card to-secondary/10">
                    <CardHeader>
                        <CardTitle>Market Trends Overview</CardTitle>
                    </CardHeader>
                    <CardContent className="pl-2">
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorVercel" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.1} />
                                            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#888888" strokeOpacity={0.1} />
                                    <XAxis
                                        dataKey="name"
                                        stroke="#888888"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        dy={10}
                                    />
                                    <YAxis
                                        stroke="#888888"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(value) => `$${value}`}
                                        dx={-10}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', color: '#f8fafc' }}
                                        itemStyle={{ color: '#f8fafc' }}
                                        cursor={{ stroke: '#64748b', strokeWidth: 1, strokeDasharray: '4 4' }}
                                    />
                                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                    <Line type="monotone" dataKey="vercel" name="Vercel" stroke="hsl(var(--primary))" strokeWidth={3} activeDot={{ r: 4, strokeWidth: 0 }} dot={false} />
                                    <Line type="monotone" dataKey="netlify" name="Netlify" stroke="#10b981" strokeWidth={3} activeDot={{ r: 4, strokeWidth: 0 }} dot={false} />
                                    <Line type="monotone" dataKey="cloudflare" name="Cloudflare" stroke="#f59e0b" strokeWidth={3} activeDot={{ r: 4, strokeWidth: 0 }} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Recent Changes Feed */}
                <Card className="col-span-3 bg-gradient-to-br from-card to-secondary/10">
                    <CardHeader>
                        <CardTitle>Recent Insights</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[
                                { company: "Vercel", change: "Pro Plan Price Increase ($20 -> $24)", severity: "high", date: "Dec 22" },
                                { company: "Netlify", change: "Holiday Discount Campaign", severity: "medium", date: "Dec 15" },
                                { company: "Cloudflare", change: "New Workers Features Announced", severity: "low", date: "Dec 10" },
                                { company: "Vercel", change: "Updated Enterprise Terms", severity: "medium", date: "Dec 05" },
                            ].map((item, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer">
                                    <div className="flex items-center space-x-3">
                                        <div className="h-9 w-9 rounded-full bg-background border flex items-center justify-center overflow-hidden p-1.5 shrink-0">
                                            {item.company === 'Vercel' && (
                                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-black dark:text-white">
                                                    <path d="M12 1L24 22H0L12 1Z" />
                                                </svg>
                                            )}
                                            {item.company === 'Netlify' && (
                                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-[#00C7B7]">
                                                    <path d="M6.4 14.8l5.2-11.2c.2-.5 1-.5 1.2 0l2 4.3 3.4-3.5c.4-.4 1.1-.1 1.1.5v13.6c0 .6-.4 1-1 1H5.7c-.6 0-1-.4-1-1V15c0-.4.5-.6.7-.2z" />
                                                    {/* Rough mock poly shape for netlify-ish look */}
                                                    <path d="M4 19h16v-2H4v2z" opacity="0.5" />
                                                </svg>
                                            )}
                                            {item.company === 'Cloudflare' && (
                                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-[#F38020]">
                                                    <path d="M18.5 10c0-2.4-1.7-4.4-4-4.9-.7-1.8-2.4-3.1-4.5-3.1-2.2 0-4.1 1.5-4.7 3.5C2.6 6 1 8.2 1 10.8c0 3.1 2.5 5.7 5.7 5.7h11.7c3.1 0 5.6-2.5 5.6-5.6s-2.5-5.6-5.5-5.9z" />
                                                </svg>
                                            )}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium leading-none">{item.company}</p>
                                            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{item.change}</p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end gap-1">
                                        <Badge variant={item.severity === 'high' ? 'destructive' : item.severity === 'medium' ? 'secondary' : 'outline'} className="text-[10px] px-1 py-0 h-5">
                                            {item.severity}
                                        </Badge>
                                        <span className="text-[10px] text-muted-foreground whitespace-nowrap">{item.date}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Dashboard;
