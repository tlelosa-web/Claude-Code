"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, Plus, RefreshCw, Send, CheckCircle2 } from "lucide-react";

interface DeliveryNote {
  id: string;
  dnNumber: string;
  date: string;
  customer: string;
  description: string;
  createdAt: string;
}

export default function DeliveryNotePage() {
  const [dns, setDns] = useState<DeliveryNote[]>([]);
  const [nextDn, setNextDn] = useState("");
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split("T")[0],
    customer: "",
    description: "",
  });
  const [loading, setLoading] = useState(false);

  const fetchDns = async () => {
    try {
      const res = await fetch("/api/dn");
      if (res.ok) {
        const data = await res.json();
        setDns(data);
      }
    } catch (error) {
      console.error("Failed to fetch DNs:", error);
      toast.error("Failed to load register history.");
    }
  };

  const fetchNextDn = async () => {
    try {
      const res = await fetch("/api/dn/next");
      if (res.ok) {
        const data = await res.json();
        setNextDn(data.nextDn);
      }
    } catch (error) {
      console.error("Failed to fetch next DN:", error);
    }
  };

  useEffect(() => {
    fetchDns();
    fetchNextDn();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nextDn || !formData.date || !formData.customer || !formData.description) {
      toast.error("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/dn/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dnNumber: nextDn,
          date: formData.date,
          customer: formData.customer,
          description: formData.description,
        }),
      });

      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Failed to register delivery note");

      toast.success("Delivery Note registered successfully!", {
        icon: <CheckCircle2 className="h-4 w-4 text-emerald-500" />
      });
      
      setFormData({ ...formData, customer: "", description: "" });
      fetchNextDn();
      fetchDns();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-white/10 pb-6">
          <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
            <FileText className="h-8 w-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight">
              Delivery Note System
            </h1>
            <p className="text-slate-400">Automated registration and tracking</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form Section */}
          <Card className="lg:col-span-1 bg-white/5 border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden relative">
            <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-blue-500 to-emerald-500" />
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Plus className="h-5 w-5 text-blue-400" /> New Delivery Note
              </CardTitle>
              <CardDescription className="text-slate-400">Create and register a new note.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="dnNumber" className="text-slate-300">DN Number (Auto)</Label>
                  <Input 
                    id="dnNumber" 
                    value={nextDn} 
                    disabled 
                    className="bg-white/5 border-white/10 text-slate-300 font-mono"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="date" className="text-slate-300">Date</Label>
                  <Input 
                    id="date" 
                    type="date" 
                    value={formData.date}
                    onChange={(e) => setFormData({...formData, date: e.target.value})}
                    required
                    className="bg-white/5 border-white/10 text-white focus:border-blue-500/50 focus:ring-blue-500/20"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="customer" className="text-slate-300">Customer</Label>
                  <Input 
                    id="customer" 
                    placeholder="Enter customer name..."
                    value={formData.customer}
                    onChange={(e) => setFormData({...formData, customer: e.target.value})}
                    required
                    className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-blue-500/20 transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-slate-300">Description</Label>
                  <Input 
                    id="description" 
                    placeholder="Item details (e.g. Fan Unit | 1)"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    required
                    className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-blue-500/20 transition-all"
                  />
                </div>

                <Button 
                  type="submit" 
                  disabled={loading || !nextDn}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)] hover:shadow-[0_0_20px_rgba(59,130,246,0.6)] transition-all group"
                >
                  {loading ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="mr-2 h-4 w-4 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
                  )}
                  {loading ? "Registering..." : "Register Delivery Note"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Register Section */}
          <Card className="lg:col-span-2 bg-white/5 border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden relative">
             <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-emerald-500 to-blue-500" />
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <div>
                <CardTitle className="text-xl">Register History</CardTitle>
                <CardDescription className="text-slate-400">Past delivery notes ordered by newest.</CardDescription>
              </div>
              <Button 
                variant="outline" 
                size="icon" 
                onClick={fetchDns} 
                className="bg-white/5 border-white/10 hover:bg-white/10 text-slate-300 transition-colors"
                title="Refresh Register"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border border-white/10 bg-black/20 overflow-hidden">
                <Table>
                  <TableHeader className="bg-white/5">
                    <TableRow className="border-white/10 hover:bg-transparent">
                      <TableHead className="text-slate-300 font-medium">DN#</TableHead>
                      <TableHead className="text-slate-300 font-medium">Date</TableHead>
                      <TableHead className="text-slate-300 font-medium">Customer</TableHead>
                      <TableHead className="text-slate-300 font-medium">Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dns.length === 0 ? (
                      <TableRow className="border-white/10 hover:bg-white/5">
                        <TableCell colSpan={4} className="h-32 text-center text-slate-500">
                          No delivery notes found. Create one to get started.
                        </TableCell>
                      </TableRow>
                    ) : (
                      dns.map((dn) => (
                        <TableRow key={dn.id} className="border-white/10 hover:bg-white/5 transition-colors group">
                          <TableCell className="font-mono text-emerald-400">{dn.dnNumber}</TableCell>
                          <TableCell className="text-slate-300">{new Date(dn.date).toLocaleDateString()}</TableCell>
                          <TableCell className="text-slate-200 font-medium">{dn.customer}</TableCell>
                          <TableCell className="text-slate-400 group-hover:text-slate-300 transition-colors max-w-[200px] truncate" title={dn.description}>
                            {dn.description}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
