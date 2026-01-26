import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Globe, Play, Trash2, Plus } from 'lucide-react';
import api from '../lib/api';

const Scans = () => {
    const [newUrl, setNewUrl] = useState('');
    const [urls, setUrls] = useState([
        { id: 1, url: 'https://vercel.com/pricing', status: 'Active', lastScan: '45 mins ago' },
        { id: 2, url: 'https://netlify.com/pricing', status: 'Active', lastScan: '1 hour ago' },
        { id: 3, url: 'https://cloudflare.com/workers-pricing', status: 'Active', lastScan: '1 hour ago' },
    ]);

    // Trigger Scan (Real API)
    const triggerScan = useMutation({
        mutationFn: async () => {
            return api.post('/api/trigger/', { user_id: 'default_user' });
        },
        onSuccess: () => {
            alert('Manual scan triggered successfully! Check your email for the report.');
        },
        onError: () => {
            alert('Failed to trigger scan. Please check backend logs.');
        },
    });

    const addUrl = () => {
        if (!newUrl) return;
        setUrls([...urls, { id: Date.now(), url: newUrl, status: 'Active', lastScan: 'Pending' }]);
        setNewUrl('');
    };

    const removeUrl = (id: number) => {
        setUrls(urls.filter(u => u.id !== id));
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Scan Management</h2>
                    <p className="text-muted-foreground">Configure competitive intelligence targets and manual triggers.</p>
                </div>
                <Button
                    onClick={() => triggerScan.mutate()}
                    disabled={triggerScan.isPending}
                    size="lg"
                    className="shadow-lg hover:shadow-primary/20 transition-all"
                >
                    <Play className="mr-2 h-4 w-4" />
                    {triggerScan.isPending ? 'Starting Scan...' : 'Trigger Manual Scan'}
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* URL Management */}
                <Card className="bg-gradient-to-br from-card to-secondary/10">
                    <CardHeader>
                        <CardTitle>Monitored URLs</CardTitle>
                        <CardDescription>Add competitor pricing pages to watch.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex gap-2">
                            <Input
                                placeholder="https://competitor.com/pricing"
                                value={newUrl}
                                onChange={(e) => setNewUrl(e.target.value)}
                            />
                            <Button onClick={addUrl}>
                                <Plus className="h-4 w-4" />
                            </Button>
                        </div>
                        <div className="space-y-2">
                            {urls.map((item) => (
                                <div key={item.id} className="flex items-center justify-between p-3 border rounded-lg bg-background/50 group hover:border-primary/50 transition-colors">
                                    <div className="flex items-center space-x-3 overflow-hidden">
                                        <div className="p-2 bg-secondary rounded-full">
                                            <Globe className="h-4 w-4 text-primary" />
                                        </div>
                                        <div className="truncate">
                                            <p className="text-sm font-medium truncate">{item.url}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <Badge variant="outline" className="text-[10px] h-5">{item.status}</Badge>
                                                <span className="text-[10px] text-muted-foreground">Last: {item.lastScan}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <Button variant="ghost" size="sm" onClick={() => removeUrl(item.id)} className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10">
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Scan History */}
                <Card className="bg-gradient-to-br from-card to-secondary/10">
                    <CardHeader>
                        <CardTitle>Recent Scan History</CardTitle>
                        <CardDescription>Latest automated and manual execution logs.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[
                                { target: 'Vercel Pricing', type: 'Manual Trigger', duration: '45s', status: 'Completed', time: 'Just now' },
                                { target: 'Netlify Enterprise', type: 'Scheduled', duration: '1m 20s', status: 'Completed', time: '2h ago' },
                                { target: 'Cloudflare Workers', type: 'Scheduled', duration: '55s', status: 'Completed', time: '2h ago' },
                                { target: 'Vercel Changelog', type: 'Scheduled', duration: '2m', status: 'Warning', time: '6h ago' },
                                { target: 'Render Pricing', type: 'Manual Trigger', duration: '30s', status: 'Failed', time: 'Yesterday' },
                            ].map((scan, i) => (
                                <div key={i} className="flex items-center justify-between p-3 border rounded-lg bg-background/50 hover:bg-muted/30 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2.5 h-2.5 rounded-full shadow-sm ${scan.status === 'Completed' ? 'bg-green-500 shadow-green-500/20' :
                                            scan.status === 'Warning' ? 'bg-yellow-500 shadow-yellow-500/20' : 'bg-red-500 shadow-red-500/20'
                                            }`} />
                                        <div>
                                            <p className="text-sm font-medium leading-none mb-1">{scan.target}</p>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-muted-foreground">{scan.type}</span>
                                                <span className="text-[10px] text-muted-foreground/50">•</span>
                                                <span className="text-xs text-muted-foreground">{scan.duration}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right flex flex-col items-end gap-1">
                                        <Badge variant={
                                            scan.status === 'Completed' ? 'secondary' :
                                                scan.status === 'Warning' ? 'outline' : 'destructive'
                                        } className="text-[10px] h-5">
                                            {scan.status}
                                        </Badge>
                                        <p className="text-[10px] text-muted-foreground">{scan.time}</p>
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

export default Scans;
