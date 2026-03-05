import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApi } from "../hooks/useApi";
import { Client } from "../lib/types";

export function ClientsPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");

  const query = useQuery({ queryKey: ["clients"], queryFn: () => api.get<Client[]>("/clients") });

  const createMutation = useMutation({
    mutationFn: () => api.post<Client>("/clients", { name, email: email || null, notes: notes || null }),
    onSuccess: () => {
      setName("");
      setEmail("");
      setNotes("");
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  return (
    <div className="space-y-4">
      <div className="card">
        <h1 className="text-2xl font-semibold">Clients</h1>
        <div className="mt-3 grid gap-2 md:grid-cols-3">
          {(query.data || []).map((client) => (
            <Link key={client.id} className="rounded-lg border border-slate-200 p-3 hover:border-slate-400" to={`/clients/${client.id}`}>
              <p className="font-medium">{client.name}</p>
              <p className="text-sm text-slate-500">{client.email || "No email"}</p>
            </Link>
          ))}
        </div>
      </div>

      <form className="card space-y-2" onSubmit={onSubmit}>
        <h2 className="text-lg font-medium">Add Client</h2>
        <input className="input" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="input" placeholder="Email (optional)" value={email} onChange={(e) => setEmail(e.target.value)} />
        <textarea className="input" placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} />
        <button className="btn">Create Client</button>
      </form>
    </div>
  );
}
