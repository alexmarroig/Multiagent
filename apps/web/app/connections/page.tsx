'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export default function ConnectionsPage() {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function fetchConnection() {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data } = await supabase
        .from('connections')
        .select('token')
        .eq('user_id', user.id)
        .eq('type', 'github')
        .single();

      if (data) setToken(data.token);
    }
    fetchConnection();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { error } = await supabase
      .from('connections')
      .upsert({
        user_id: user.id,
        type: 'github',
        token: token,
      }, { onConflict: 'user_id,type' });

    if (error) alert(error.message);
    else setSaved(true);
    setLoading(false);
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Connections</h1>
      <div className="max-w-xl bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold mb-2">GitHub Personal Access Token</h2>
        <p className="text-sm text-gray-500 mb-4">
          This token will be used to clone your repositories and push changes.
          Marked as TODO: Encryption.
        </p>
        <div className="space-y-4">
          <input
            type="password"
            placeholder="ghp_xxxxxxxxxxxx"
            className="w-full p-2 border rounded"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <button
            onClick={handleSave}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Connection'}
          </button>
          {saved && <span className="ml-4 text-green-600 font-medium">Saved!</span>}
        </div>
      </div>
    </div>
  );
}
