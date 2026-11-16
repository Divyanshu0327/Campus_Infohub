import React, { useEffect, useState } from 'react';
import API from '../../services/api';
import { Loader2, CheckCircle, XCircle, Search, Clock, Award, GraduationCap, Users, FileText, Eye, Download, ArrowLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import Breadcrumbs from '../../components/Breadcrumbs';

// ─── Tab button ───────────────────────────────────────────────────────────────
const TabBtn = ({ active, onClick, icon: Icon, label, count }) => (
  <button
    onClick={onClick}
    className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all ${
      active
        ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30'
        : 'bg-white text-slate-500 border border-slate-200 hover:border-amber-300 hover:text-amber-600'
    }`}
  >
    <Icon size={16} />
    <span>{label}</span>
    {count > 0 && (
      <span className={`px-2 py-0.5 rounded-full text-xs ${active ? 'bg-white/20 text-white' : 'bg-amber-100 text-amber-700'}`}>
        {count}
      </span>
    )}
  </button>
);

// ─── User Pending Card ────────────────────────────────────────────────────────
const UserCard = ({ user, onApprove, onReject }) => (
  <motion.div
    layout
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 0.9 }}
    className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:shadow-amber-900/10 transition-all duration-300 relative overflow-hidden"
  >
    <div className="absolute top-0 right-0 w-32 h-32 bg-amber-50 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none" />
    <div className="relative z-10">
      <div className="flex justify-between items-start mb-4">
        <div className={`h-14 w-14 rounded-2xl flex items-center justify-center text-white font-bold text-xl shadow-lg ${
          user.role === 'alumni' ? 'bg-gradient-to-br from-purple-500 to-indigo-600' : 'bg-gradient-to-br from-amber-400 to-orange-500'
        }`}>
          {(user.name || '?').charAt(0)}
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
          user.role === 'alumni' ? 'bg-indigo-50 text-indigo-600 border border-indigo-100' : 'bg-amber-50 text-amber-600 border border-amber-100'
        }`}>
          {user.role}
        </span>
      </div>
      <h3 className="text-xl font-serif font-bold text-slate-800 mb-1">{user.name}</h3>
      <p className="text-sm text-slate-500 mb-5 font-medium">{user.email}</p>
      <div className="space-y-2 mb-6 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
        <div className="flex items-center text-sm text-slate-600">
          <Award size={14} className="mr-2 text-slate-400" />
          <span className="font-semibold">{user.course}</span><span className="mx-1">•</span><span>{user.batch}</span>
        </div>
        <div className="flex items-center text-sm text-slate-600">
          <GraduationCap size={14} className="mr-2 text-slate-400" />
          <span className="font-mono text-xs bg-white px-2 py-0.5 rounded border border-slate-200">{user.reg_no || user.regNo}</span>
        </div>
        <div className="flex items-center text-xs text-slate-400">
          <Clock size={12} className="mr-2" />Requested: {new Date(user.created_at || Date.now()).toLocaleDateString()}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <button onClick={() => onReject(user.id, user.name)} className="flex items-center justify-center py-2.5 rounded-xl border border-rose-100 text-rose-600 font-bold text-sm hover:bg-rose-50 transition">
          <XCircle size={16} className="mr-2" />Reject
        </button>
        <button onClick={() => onApprove(user.id, user.name)} className="flex items-center justify-center py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 hover:from-emerald-600 hover:to-teal-600 transition">
          <CheckCircle size={16} className="mr-2" />Approve
        </button>
      </div>
    </div>
  </motion.div>
);

// ─── Alumni Pending Card ────────────────────────────────────────────────────────
const AlumniCard = ({ alumni, onApprove, onReject }) => (
  <motion.div
    layout
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 0.9 }}
    className="bg-white rounded-3xl p-6 border border-slate-100 shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:shadow-indigo-900/10 transition-all duration-300 relative overflow-hidden"
  >
    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none" />
    <div className="relative z-10">
      <div className="flex justify-between items-start mb-4">
        <div className="h-14 w-14 rounded-2xl flex items-center justify-center text-white font-bold text-xl shadow-lg bg-gradient-to-br from-indigo-400 to-purple-600">
          {(alumni.name || '?').charAt(0)}
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-600 border border-indigo-100">
          ALUMNI
        </span>
      </div>
      <h3 className="text-xl font-serif font-bold text-slate-800 mb-1">{alumni.name}</h3>
      <p className="text-sm text-slate-500 mb-5 font-medium">{alumni.email}</p>
      <div className="space-y-2 mb-6 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
        <div className="flex items-center text-sm text-slate-600">
          <Award size={14} className="mr-2 text-slate-400" />
          <span className="font-semibold">{alumni.course_completed}</span><span className="mx-1">•</span><span>{alumni.year_of_admission}-{alumni.year_of_completion}</span>
        </div>
        <div className="flex items-center text-sm text-slate-600">
          <GraduationCap size={14} className="mr-2 text-slate-400" />
          <span className="font-mono text-xs bg-white px-2 py-0.5 rounded border border-slate-200">{alumni.enrollment_number}</span>
        </div>
        <div className="flex items-center text-xs text-slate-400">
          <Clock size={12} className="mr-2" />Requested: {new Date(alumni.created_at || Date.now()).toLocaleDateString()}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <button onClick={() => onReject(alumni.id, alumni.name)} className="flex items-center justify-center py-2.5 rounded-xl border border-rose-100 text-rose-600 font-bold text-sm hover:bg-rose-50 transition">
          <XCircle size={16} className="mr-2" />Reject
        </button>
        <button onClick={() => onApprove(alumni.id, alumni.name)} className="flex items-center justify-center py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 hover:from-emerald-600 hover:to-teal-600 transition">
          <CheckCircle size={16} className="mr-2" />Approve
        </button>
      </div>
    </div>
  </motion.div>
);

// ─── Post Pending Card ────────────────────────────────────────────────────────
const PostCard = ({ post, onApprove, onReject }) => (
  <motion.div
    layout
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="bg-white rounded-2xl p-6 border border-slate-100 shadow-md hover:shadow-xl transition-all duration-300"
  >
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-center space-x-3">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white font-bold text-sm shadow-md">
          {post.user?.name?.charAt(0) || 'U'}
        </div>
        <div>
          <p className="font-bold text-slate-800 text-sm">{post.user?.name || 'Unknown User'}</p>
          <p className="text-xs text-slate-400">{new Date(post.created_at).toLocaleString()}</p>
        </div>
      </div>
      <span className="text-xs font-bold bg-orange-50 text-orange-600 border border-orange-100 px-2.5 py-1 rounded-full">
        Pending Review
      </span>
    </div>

    {/* Post content preview */}
    <p className="text-slate-700 text-sm leading-relaxed mb-4 line-clamp-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
      {post.content}
    </p>

    {post.image && (
      <div className="mb-4 rounded-xl overflow-hidden border border-slate-100">
        <img src={post.image} alt="Post attachment" className="w-full h-40 object-cover" />
      </div>
    )}

    <div className="flex items-center space-x-3">
      <button
        onClick={() => onReject(post.id)}
        className="flex-1 flex items-center justify-center py-2.5 rounded-xl border border-rose-100 text-rose-600 font-bold text-sm hover:bg-rose-50 transition"
      >
        <XCircle size={16} className="mr-2" />Reject Post
      </button>
      <button
        onClick={() => onApprove(post.id)}
        className="flex-1 flex items-center justify-center py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 hover:from-emerald-600 hover:to-teal-600 transition"
      >
        <CheckCircle size={16} className="mr-2" />Approve & Publish
      </button>
    </div>
  </motion.div>
);

// ─── Main Component ───────────────────────────────────────────────────────────
const AdminPending = () => {
  const [tab, setTab] = useState('users');
  const [pendingUsers, setPendingUsers] = useState([]);
  const [pendingAlumni, setPendingAlumni] = useState([]);
  const [pendingPosts, setPendingPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [usersRes, alumniRes, postsRes] = await Promise.all([
        API.get('/admin/pending-users'),
        API.get('/admin/alumni?status_filter=Pending'),
        API.get('/admin/posts/pending'),
      ]);
      setPendingUsers(usersRes.data);
      setPendingAlumni(alumniRes.data);
      setPendingPosts(postsRes.data);
    } catch (err) {
      console.error('Failed to load pending items', err);
    } finally {
      setLoading(false);
    }
  };

  // ── User Actions ──────────────────────────────────────────
  const handleApproveUser = async (id, name) => {
    if (!window.confirm(`Approve ${name}?`)) return;
    try {
      await API.post(`/admin/approve/${id}`);
      setPendingUsers(cur => cur.filter(u => u.id !== id));
      toast.success(`${name} approved successfully`);
    } catch { toast.error('Failed to approve user'); }
  };

  const handleRejectUser = async (id, name) => {
    if (!window.confirm(`Reject registration for ${name}?`)) return;
    try {
      await API.post(`/admin/reject/${id}`);
      setPendingUsers(cur => cur.filter(u => u.id !== id));
      toast.success(`${name}'s registration rejected`);
    } catch { toast.error('Failed to reject user'); }
  };

  // ── Alumni Actions ──────────────────────────────────────────
  const handleApproveAlumni = async (id, name) => {
    if (!window.confirm(`Approve Alumni Registration for ${name}?`)) return;
    try {
      await API.post(`/admin/alumni/${id}/approve`);
      setPendingAlumni(cur => cur.filter(a => a.id !== id));
      toast.success(`${name} approved successfully. An email has been sent.`);
    } catch (err) { 
      toast.error(err.response?.data?.detail || 'Failed to approve alumni'); 
    }
  };

  const handleRejectAlumni = async (id, name) => {
    if (!window.confirm(`Reject alumni registration for ${name}?`)) return;
    try {
      await API.post(`/admin/alumni/${id}/reject`);
      setPendingAlumni(cur => cur.filter(a => a.id !== id));
      toast.success(`${name}'s registration rejected. An email has been sent.`);
    } catch (err) { 
      toast.error(err.response?.data?.detail || 'Failed to reject alumni'); 
    }
  };

  // ── Post Actions ──────────────────────────────────────────
  const handleApprovePost = async (id) => {
    try {
      await API.post(`/admin/posts/${id}/approve`);
      setPendingPosts(cur => cur.filter(p => p.id !== id));
      toast.success('Post approved and published!');
    } catch { toast.error('Failed to approve post'); }
  };

  const handleRejectPost = async (id) => {
    if (!window.confirm('Reject and permanently remove this post?')) return;
    try {
      await API.delete(`/admin/posts/${id}`);
      setPendingPosts(cur => cur.filter(p => p.id !== id));
      toast.success('Post rejected and removed');
    } catch { toast.error('Failed to reject post'); }
  };

  const filteredUsers = pendingUsers.filter(u =>
    u.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.reg_no || u.regNo)?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredAlumni = pendingAlumni.filter(a =>
    a.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.enrollment_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredPosts = pendingPosts.filter(p =>
    p.content?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.user?.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleExportExcel = async () => {
    if (filteredUsers.length === 0 && filteredAlumni.length === 0 && filteredPosts.length === 0) {
      toast.error('No records available for the selected filters.');
      return;
    }

    try {
      const res = await API.get('/admin/pending/export', {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      const filename = `Pending_Approvals_${new Date().toISOString().split('T')[0]}.xlsx`;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Excel exported successfully!');
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Failed to export Excel file.';
      toast.error(typeof errMsg === 'string' ? errMsg : 'No pending records available.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      {/* Navigation Breadcrumbs & Back Button */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <Breadcrumbs items={[{ label: 'Admin', path: '/admin' }, { label: 'Pending Approvals' }]} />
        <Link to="/admin" className="px-3.5 py-1.5 bg-white hover:bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 shadow-sm flex items-center gap-1.5 transition">
          <ArrowLeft size={14} /> ← Back to Dashboard
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-slate-800">Pending Approvals</h1>
          <p className="text-slate-500 font-medium mt-1">Review and moderate new registrations and post submissions.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input
              type="text"
              placeholder="Search..."
              className="pl-9 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium w-64 outline-none focus:border-amber-500 transition shadow-sm"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
          <button 
            onClick={handleExportExcel}
            className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-md transition"
          >
            <Download size={14} /> Download Excel
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center space-x-3 mb-8">
        <TabBtn
          active={tab === 'users'}
          onClick={() => setTab('users')}
          icon={Users}
          label="Student Registrations"
          count={pendingUsers.length}
        />
        <TabBtn
          active={tab === 'alumni'}
          onClick={() => setTab('alumni')}
          icon={GraduationCap}
          label="Alumni Registrations"
          count={pendingAlumni.length}
        />
        <TabBtn
          active={tab === 'posts'}
          onClick={() => setTab('posts')}
          icon={FileText}
          label="Post Submissions"
          count={pendingPosts.length}
        />
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-amber-500" size={40} /></div>
      ) : (
        <AnimatePresence mode="wait">
          {tab === 'users' && (
            <motion.div key="users" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {filteredUsers.length === 0 ? (
                <div className="text-center py-24 bg-white rounded-3xl border border-dashed border-slate-200">
                  <div className="h-20 w-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-400">
                    <CheckCircle size={32} />
                  </div>
                  <p className="text-slate-600 font-bold text-lg">All Caught Up!</p>
                  <p className="text-slate-400 text-sm mt-1">No pending user registrations.</p>
                </div>
              ) : (
                <motion.div layout className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  <AnimatePresence>
                    {filteredUsers.map(user => (
                      <UserCard key={user.id} user={user} onApprove={handleApproveUser} onReject={handleRejectUser} />
                    ))}
                  </AnimatePresence>
                </motion.div>
              )}
            </motion.div>
          )}

          {tab === 'alumni' && (
            <motion.div key="alumni" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {filteredAlumni.length === 0 ? (
                <div className="text-center py-24 bg-white rounded-3xl border border-dashed border-slate-200">
                  <div className="h-20 w-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-400">
                    <CheckCircle size={32} />
                  </div>
                  <p className="text-slate-600 font-bold text-lg">All Caught Up!</p>
                  <p className="text-slate-400 text-sm mt-1">No pending alumni registrations.</p>
                </div>
              ) : (
                <motion.div layout className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  <AnimatePresence>
                    {filteredAlumni.map(alumni => (
                      <AlumniCard key={alumni.id} alumni={alumni} onApprove={handleApproveAlumni} onReject={handleRejectAlumni} />
                    ))}
                  </AnimatePresence>
                </motion.div>
              )}
            </motion.div>
          )}

          {tab === 'posts' && (
            <motion.div key="posts" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {filteredPosts.length === 0 ? (
                <div className="text-center py-24 bg-white rounded-3xl border border-dashed border-slate-200">
                  <div className="h-20 w-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-400">
                    <Eye size={32} />
                  </div>
                  <p className="text-slate-600 font-bold text-lg">Feed is Clean!</p>
                  <p className="text-slate-400 text-sm mt-1">No posts awaiting review.</p>
                </div>
              ) : (
                <motion.div layout className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <AnimatePresence>
                    {filteredPosts.map(post => (
                      <PostCard key={post.id} post={post} onApprove={handleApprovePost} onReject={handleRejectPost} />
                    ))}
                  </AnimatePresence>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
};

export default AdminPending;
