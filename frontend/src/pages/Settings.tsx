import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Save } from 'lucide-react';

const Settings = () => {
    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                <p className="text-muted-foreground">Manage your account preferences and notifications.</p>
            </div>

            <div className="grid gap-6">
                <Card className="bg-gradient-to-br from-card to-secondary/10">
                    <CardHeader>
                        <CardTitle>Notification Preferences</CardTitle>
                        <CardDescription>Choose how you want to be alerted about changes.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-4 border rounded">
                            <div>
                                <p className="font-medium">Email Notifications</p>
                                <p className="text-sm text-muted-foreground">Receive daily digests and critical alerts.</p>
                            </div>
                            <div className="h-6 w-11 bg-primary rounded-full relative cursor-pointer">
                                <div className="absolute right-1 top-1 h-4 w-4 bg-white rounded-full"></div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-4 border rounded">
                            <div>
                                <p className="font-medium">Critical Alerts Only</p>
                                <p className="text-sm text-muted-foreground">Only notify me when high-severity changes are detected.</p>
                            </div>
                            <div className="h-6 w-11 bg-muted rounded-full relative cursor-pointer">
                                <div className="absolute left-1 top-1 h-4 w-4 bg-white rounded-full"></div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-card to-secondary/10">
                    <CardHeader>
                        <CardTitle>Agent Configuration</CardTitle>
                        <CardDescription>Customize the behavior of AI agents.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <label className="text-sm font-medium">Analyst Model</label>
                            <select className="w-full p-2 rounded border bg-background">
                                <option>GPT-4o (Recommended)</option>
                                <option>GPT-4 Turbo</option>
                                <option>GPT-3.5 Turbo</option>
                            </select>
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium">Scan Frequency</label>
                            <select className="w-full p-2 rounded border bg-background">
                                <option>Every 3 Hours</option>
                                <option>Every 2 Hours</option>
                                <option>Every 1 Hour</option>
                                <option>Every 30 Minutes</option>
                                <option>Custom</option>
                            </select>
                        </div>
                    </CardContent>
                </Card>

                <div className="flex justify-end">
                    <Button>
                        <Save className="mr-2 h-4 w-4" /> Save Changes
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default Settings;
