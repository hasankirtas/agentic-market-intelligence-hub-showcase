import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { FileText, Calendar, ArrowRight, X } from 'lucide-react';
import { Button } from '../components/ui/button';

const Reports = () => {
    const [selectedReport, setSelectedReport] = useState<any>(null);

    // Realistic Mock Data for December 2025
    const reports = [
        {
            id: 'rpt_dec_04',
            title: 'Q4 2025 Competitive Landscape Wrap-up',
            date: 'Dec 31, 2025',
            summary: 'Analysis suggests a consolidation of enterprise pricing tiers. Vercel and Netlify ended the year with aggressive enterprise restructuring. Recommend reviewing Q1 budget allocation for hosting services.',
            details: `EXECUTIVE SUMMARY:
Q4 2025 marked a pivotal shift in the JAMstack ecosystem. Both Vercel and Netlify moved to consolidate their upper-tier offerings, effectively forcing mid-sized startups into Enterprise plans earlier in their growth cycle.

KEY FINDINGS:
1. Vercel's "Pro" plan price hike (20%) was aimed directly at filtering out high-bandwidth hobbyist projects.
2. Netlify's retention strategy focused on long-term contracts, offering significant Q1 2026 discounts for annual lock-ins.
3. Cloudflare remains the low-cost disruptor but is steadily increasing complexity in its developer experience.

RECOMMENDATION:
For Q1 2026, we strongly advise auditing all "Pro" workspaces. Users with >500GB bandwidth should evaluate Cloudflare Pages as a cost-saving migration target.
            `,
            type: 'Quarterly',
            company: 'All'
        },
        {
            id: 'rpt_dec_03',
            title: 'Critical Alert: Vercel Pricing Surge',
            date: 'Dec 22, 2025',
            summary: 'IMMEDIATE ACTION: Vercel Pro plan base increased to $24/seat. New usage limits on Edge Middleware may trigger overages. Audit current function invocations to mitigate cost impact.',
            details: `ALERT DETAILS:
Effective immediately, Vercel has updated its pricing model for the Pro tier.
- Seat Cost: $20 -> $24 / month
- Edge Middleware Invocations: Now capped at 1M / month (previously 2M).
- Overage Fee: $5 per additional 1M requests.

IMPACT ANALYSIS:
Based on your current usage patterns (approx. 1.5M invocations/mo), this change will result in an estimated $20/mo increase per project in overage fees unless optimized.

ACTION ITEMS:
1. Review all middleware functions for unnecessary invocations (e.g., static asset headers).
2. Consider moving static routing logic to \`next.config.js\` redirects instead of Middleware.
            `,
            type: 'Emergency',
            company: 'Vercel'
        },
        {
            id: 'rpt_dec_02',
            title: 'Weekly Market Analysis',
            date: 'Dec 15, 2025',
            summary: 'Netlify\'s holiday campaign targets SMB acquisition with aggressive discounting. Cloudflare maintains stable pricing but introduces beta features for Workers AI. No improved incentives detected from Vercel this week.',
            details: `MARKET SNAPSHOT (Week of Dec 15):
- Netlify: Launched "Winter Deploy" campaign. 20% off Pro plans for first 3 months. Good opportunity for new sub-projects.
- Vercel: Quiet on the pricing front. Released v34 of their CLI with minor bug fixes.
- Cloudflare: Announced "Workers AI" vector database integration in open beta. This is a direct competitor to Vercel's AI SDK + Pinecone stack.

STRATEGIC ADVICE:
No immediate action required. Monitor Cloudflare's AI pricing as it exits beta in early 2026.
            `,
            type: 'Weekly',
            company: 'Netlify'
        },
        {
            id: 'rpt_dec_01',
            title: 'Feature Watch: Cloudflare Workers',
            date: 'Dec 10, 2025',
            summary: 'Cloudflare Workers now supports persistent SQL storage natively. This feature directly competes with Vercel KV and creates a lower-latency alternative for edge-heavy applications.',
            details: `TECHNICAL BRIEF: D1 SQL Database
Cloudflare has moved D1 (their native SQL database) to General Availability (GA).
- Performance: Sub-10ms reads globally.
- Pricing: $0.75 / GB storage (significantly cheaper than Vercel KV).
- Compatibility: Works natively with Workers.

COMPETITIVE INTEL:
This move undercuts Vercel's storage story. Vercel relies on Upstash (KV) and Postgres partners (Neon). Cloudflare owning the full stack (Compute + Storage) at the edge gives them a latency advantage for purely dynamic apps.
            `,
            type: 'Insight',
            company: 'Cloudflare'
        },
        {
            id: 'rpt_nov_04',
            title: 'Weekly Market Analysis',
            date: 'Dec 01, 2025',
            summary: 'Market remains stable entering December. Deployment frequency across major providers shows typical seasonal dip. Good window for infrastructure maintenance updates.',
            details: `MARKET SNAPSHOT (Week of Dec 01):
A quiet week across the board as major dev-tool companies prepare for holiday freezes.
- Deployment activity down 15% industry-wide.
- Support response times slightly slower (avg 4h -> 6h).

OPPORTUNITY:
Use this stable window to perform dependency upgrades (Next.js 16, etc.) and infrastructure cleanups before the Jan 2026 rush.
            `,
            type: 'Weekly',
            company: 'All'
        },
    ];

    return (
        <div className="space-y-6 animate-in fade-in duration-500 relative">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Intelligence Reports</h2>
                <p className="text-muted-foreground">Generated analysis from the Analyst Agent.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {reports.map((report) => (
                    <Card key={report.id} className={`hover:shadow-md transition-shadow cursor-pointer border-l-4 bg-gradient-to-br from-card to-secondary/10 ${report.type === 'Emergency' ? 'border-l-destructive' :
                        report.type === 'Quarterly' ? 'border-l-primary' :
                            'border-l-secondary'
                        }`}>
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <CardTitle className="text-base line-clamp-1">{report.title}</CardTitle>
                                    </div>
                                    <CardDescription className="flex items-center gap-1 text-xs">
                                        <Calendar className="h-3 w-3" /> {report.date}
                                    </CardDescription>
                                </div>
                                <Badge variant={report.type === 'Emergency' ? 'destructive' : 'outline'}>{report.type}</Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="mb-4">
                                <Badge variant="secondary" className="text-[10px] mb-2">{report.company}</Badge>
                                <p className="text-sm text-muted-foreground line-clamp-3">
                                    {report.summary}
                                </p>
                            </div>
                            <Button
                                variant="ghost"
                                className="w-full text-xs h-8 group"
                                onClick={() => setSelectedReport(report)}
                            >
                                <FileText className="mr-2 h-3 w-3" /> Read Full Analysis
                                <ArrowRight className="ml-1 h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </Button>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Modal Overlay */}
            {selectedReport && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto shadow-2xl bg-background border-none relative animate-in zoom-in-95 duration-200">
                        <button
                            onClick={() => setSelectedReport(null)}
                            className="absolute right-4 top-4 p-2 rounded-full hover:bg-muted transition-colors"
                        >
                            <X className="h-4 w-4" />
                        </button>

                        <CardHeader className="border-b">
                            <div className="flex items-center gap-2 mb-2">
                                <Badge variant={selectedReport.type === 'Emergency' ? 'destructive' : 'outline'}>
                                    {selectedReport.type}
                                </Badge>
                                <span className="text-sm text-muted-foreground">{selectedReport.date}</span>
                            </div>
                            <CardTitle className="text-2xl">{selectedReport.title}</CardTitle>
                            <CardDescription className="text-base mt-2">
                                {selectedReport.company} Market Update
                            </CardDescription>
                        </CardHeader>

                        <CardContent className="pt-6 space-y-4">
                            <div className="p-4 bg-muted/30 rounded-lg italic text-sm border-l-2 border-primary">
                                "{selectedReport.summary}"
                            </div>

                            <div className="prose prose-sm dark:prose-invert max-w-none">
                                <h4 className="text-lg font-semibold mb-2">Detailed Analysis</h4>
                                <div className="whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
                                    {selectedReport.details}
                                </div>
                            </div>

                            <div className="pt-4 flex justify-end">
                                <Button onClick={() => setSelectedReport(null)}>
                                    Close Report
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default Reports;
