<!-- templates/superadmin/dashboard.html -->
{% extends "base.html" %}

{% block title %}Superadmin Dashboard | Elmed Wellmind{% endblock %}

{% block content %}
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css" rel="stylesheet">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

<style>
    :root {
        --primary: #667eea;
        --primary-dark: #5a67d8;
        --secondary: #764ba2;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --info: #3B82F6;
        --dark: #1F2937;
        --light: #F9FAFB;
        --gray: #6B7280;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', sans-serif;
        background: #F3F4F6;
    }

    .dashboard-container {
        padding: 100px 30px 40px;
        max-width: 1600px;
        margin: 0 auto;
    }

    /* Welcome Header */
    .welcome-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 40px;
        color: white;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
    }

    .welcome-title h1 {
        font-size: 2.5rem;
        margin-bottom: 10px;
    }

    .welcome-title p {
        opacity: 0.9;
        font-size: 1.1rem;
    }

    .admin-badge {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        padding: 12px 25px;
        border-radius: 50px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }

    .stat-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        display: flex;
        align-items: center;
        gap: 20px;
    }

    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 30px rgba(0, 0, 0, 0.1);
    }

    .stat-icon {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.8rem;
    }

    .stat-content h3 {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 5px;
        color: var(--dark);
    }

    .stat-content p {
        color: var(--gray);
        font-size: 0.9rem;
    }

    /* Tabs */
    .tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 10px;
        overflow-x: auto;
        flex-wrap: wrap;
    }

    .tab-btn {
        padding: 12px 25px;
        background: none;
        border: none;
        font-weight: 600;
        color: var(--gray);
        cursor: pointer;
        border-radius: 25px;
        transition: all 0.3s ease;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .tab-btn:hover {
        background: #F3F4F6;
        color: var(--primary);
    }

    .tab-btn.active {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }

    .tab-content {
        display: none;
        animation: fadeIn 0.3s ease;
    }

    .tab-content.active {
        display: block;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Action Bar */
    .action-bar {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .search-box {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #F9FAFB;
        padding: 8px 15px;
        border-radius: 25px;
        border: 1px solid #E5E7EB;
    }

    .search-box input {
        border: none;
        background: transparent;
        padding: 8px;
        width: 250px;
        outline: none;
    }

    .filter-dropdown {
        padding: 8px 15px;
        border: 1px solid #E5E7EB;
        border-radius: 25px;
        background: white;
        outline: none;
    }

    /* Table Styles */
    .table-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        overflow-x: auto;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
    }

    .data-table th {
        text-align: left;
        padding: 15px;
        background: #F9FAFB;
        color: var(--dark);
        font-weight: 600;
        font-size: 0.9rem;
    }

    .data-table td {
        padding: 15px;
        border-bottom: 1px solid #F3F4F6;
    }

    .data-table tr:hover {
        background: #F9FAFB;
    }

    /* Status Badges */
    .status-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }

    .status-active {
        background: #D1FAE5;
        color: #065F46;
    }

    .status-inactive {
        background: #FEE2E2;
        color: #991B1B;
    }

    .status-pending {
        background: #FEF3C7;
        color: #92400E;
    }

    .role-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .role-superadmin {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }

    .role-admin {
        background: #3B82F6;
        color: white;
    }

    .role-professional {
        background: #10B981;
        color: white;
    }

    .role-client {
        background: #6B7280;
        color: white;
    }

    .role-org {
        background: #F59E0B;
        color: white;
    }

    /* Action Buttons */
    .action-btns {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }

    .action-btn {
        padding: 6px 12px;
        border: none;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    .action-btn:hover {
        transform: translateY(-2px);
    }

    .btn-view {
        background: #EFF6FF;
        color: #1E40AF;
    }

    .btn-edit {
        background: #FEF3C7;
        color: #92400E;
    }

    .btn-impersonate {
        background: #E0E7FF;
        color: #4338CA;
    }

    .btn-reset {
        background: #FEE2E2;
        color: #991B1B;
    }

    .btn-balance {
        background: #D1FAE5;
        color: #065F46;
    }

    .btn-chat {
        background: #E0F2FE;
        color: #0369A1;
    }

    .btn-rate {
        background: #FEF9C3;
        color: #854D0E;
    }

    .btn-toggle {
        background: #F3F4F6;
        color: #1F2937;
    }

    /* Modal Styles */
    .modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        backdrop-filter: blur(5px);
        z-index: 9999;
        align-items: center;
        justify-content: center;
    }

    .modal.active {
        display: flex;
    }

    .modal-content {
        background: white;
        border-radius: 20px;
        width: 90%;
        max-width: 600px;
        max-height: 90vh;
        overflow-y: auto;
        animation: slideUp 0.3s ease;
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .modal-header {
        padding: 25px 30px;
        border-bottom: 1px solid #E5E7EB;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px 20px 0 0;
    }

    .modal-header h3 {
        font-size: 1.5rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .modal-close {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
    }

    .modal-close:hover {
        background: rgba(255,255,255,0.3);
        transform: rotate(90deg);
    }

    .modal-body {
        padding: 30px;
    }

    .form-group {
        margin-bottom: 20px;
    }

    .form-group label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: var(--dark);
    }

    .form-control {
        width: 100%;
        padding: 12px 15px;
        border: 2px solid #E5E7EB;
        border-radius: 10px;
        font-size: 1rem;
        transition: all 0.3s;
    }

    .form-control:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .btn-save {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        font-size: 1.1rem;
        transition: all 0.3s;
    }

    .btn-save:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }

    /* Activity Feed */
    .activity-feed {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .activity-item {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 15px;
        border-bottom: 1px solid #F3F4F6;
        transition: all 0.3s;
    }

    .activity-item:hover {
        background: #F9FAFB;
        transform: translateX(5px);
    }

    .activity-icon {
        width: 45px;
        height: 45px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }

    .activity-login { background: #E0F2FE; color: #0369A1; }
    .activity-register { background: #D1FAE5; color: #065F46; }
    .activity-payment { background: #FEF3C7; color: #92400E; }
    .activity-session { background: #F3E8FF; color: #6B21A8; }

    .activity-details {
        flex: 1;
    }

    .activity-title {
        font-weight: 600;
        margin-bottom: 3px;
    }

    .activity-time {
        font-size: 0.8rem;
        color: var(--gray);
    }

    /* Analytics Grid */
    .analytics-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 20px;
        margin-bottom: 30px;
    }

    .chart-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Responsive */
    @media (max-width: 1024px) {
        .analytics-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 768px) {
        .dashboard-container {
            padding: 80px 15px 30px;
        }

        .welcome-title h1 {
            font-size: 2rem;
        }

        .form-row {
            grid-template-columns: 1fr;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }
    }
</style>

<div class="dashboard-container">
    <!-- Welcome Header -->
    <div class="welcome-header">
        <div class="welcome-title">
            <h1>Welcome back, {{ current_user.get_full_name() }}! 👋</h1>
            <p>You have full control over the Elmed Wellmind platform</p>
        </div>
        <div class="admin-badge">
            <i class="fas fa-crown"></i> Super Administrator
        </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid" id="statsGrid">
        <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-users"></i></div>
            <div class="stat-content">
                <h3 id="totalUsers">0</h3>
                <p>Total Users</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-user-md"></i></div>
            <div class="stat-content">
                <h3 id="totalProfessionals">0</h3>
                <p>Professionals</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-building"></i></div>
            <div class="stat-content">
                <h3 id="totalOrganizations">0</h3>
                <p>Organizations</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-clock"></i></div>
            <div class="stat-content">
                <h3 id="activeToday">0</h3>
                <p>Active Today</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-credit-card"></i></div>
            <div class="stat-content">
                <h3 id="totalRevenue">KES 0</h3>
                <p>Total Revenue</p>
            </div>
        </div>
    </div>

    <!-- Analytics Section -->
    <div class="analytics-grid">
        <div class="chart-card">
            <div class="chart-title">
                <i class="fas fa-chart-line" style="color: var(--primary);"></i>
                User Growth (Last 30 Days)
            </div>
            <canvas id="userGrowthChart" style="width:100%; height:300px;"></canvas>
        </div>
        <div class="chart-card">
            <div class="chart-title">
                <i class="fas fa-chart-pie" style="color: var(--secondary);"></i>
                User Distribution
            </div>
            <canvas id="userDistributionChart" style="width:100%; height:300px;"></canvas>
        </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <button class="tab-btn active" onclick="showTab('users')">
            <i class="fas fa-users"></i> Users
        </button>
        <button class="tab-btn" onclick="showTab('professionals')">
            <i class="fas fa-user-md"></i> Professionals
        </button>
        <button class="tab-btn" onclick="showTab('organizations')">
            <i class="fas fa-building"></i> Organizations
        </button>
        <button class="tab-btn" onclick="showTab('clients')">
            <i class="fas fa-user"></i> Clients
        </button>
        <button class="tab-btn" onclick="showTab('activity')">
            <i class="fas fa-history"></i> Activity Log
        </button>
        <button class="tab-btn" onclick="showTab('analytics')">
            <i class="fas fa-chart-bar"></i> Analytics
        </button>
        <button class="tab-btn" onclick="showTab('system')">
            <i class="fas fa-cog"></i> System Settings
        </button>
    </div>

    <!-- Users Tab -->
    <div class="tab-content active" id="usersTab">
        <div class="action-bar">
            <div class="search-box">
                <i class="fas fa-search" style="color: var(--gray);"></i>
                <input type="text" id="userSearch" placeholder="Search users...">
            </div>
            <div style="display: flex; gap: 10px;">
                <select class="filter-dropdown" id="roleFilter">
                    <option value="">All Roles</option>
                    <option value="client">Clients</option>
                    <option value="professional">Professionals</option>
                    <option value="organization_admin">Organizations</option>
                    <option value="superadmin">Super Admins</option>
                </select>
                <select class="filter-dropdown" id="statusFilter">
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                </select>
            </div>
        </div>

        <div class="table-container">
            <table class="data-table" id="usersTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>User</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Verified</th>
                        <th>Balance</th>
                        <th>Joined</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="usersTableBody"></tbody>
            </table>
        </div>
    </div>

    <!-- Professionals Tab -->
    <div class="tab-content" id="professionalsTab">
        <div class="action-bar">
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" id="professionalSearch" placeholder="Search professionals...">
            </div>
            <select class="filter-dropdown" id="verificationFilter">
                <option value="">All</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
            </select>
        </div>
        <div class="table-container">
            <table class="data-table" id="professionalsTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>License</th>
                        <th>Fee</th>
                        <th>Rating</th>
                        <th>Status</th>
                        <th>Verified</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="professionalsTableBody"></tbody>
            </table>
        </div>
    </div>

    <!-- Organizations Tab -->
    <div class="tab-content" id="organizationsTab">
        <div class="action-bar">
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" id="orgSearch" placeholder="Search organizations...">
            </div>
        </div>
        <div class="table-container">
            <table class="data-table" id="organizationsTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Company</th>
                        <th>Employees</th>
                        <th>Code</th>
                        <th>Sessions</th>
                        <th>Wellness Score</th>
                        <th>Balance</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="organizationsTableBody"></tbody>
            </table>
        </div>
    </div>

    <!-- Clients Tab -->
    <div class="tab-content" id="clientsTab">
        <div class="table-container">
            <table class="data-table" id="clientsTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Wellness Score</th>
                        <th>Risk Level</th>
                        <th>Sessions</th>
                        <th>Last Active</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="clientsTableBody"></tbody>
            </table>
        </div>
    </div>

    <!-- Activity Log Tab -->
    <div class="tab-content" id="activityTab">
        <div class="activity-feed" id="activityFeed"></div>
    </div>

    <!-- Analytics Tab -->
    <div class="tab-content" id="analyticsTab">
        <div class="analytics-grid">
            <div class="chart-card">
                <div class="chart-title">
                    <i class="fas fa-calendar"></i> Sessions Overview
                </div>
                <canvas id="sessionsChart"></canvas>
            </div>
            <div class="chart-card">
                <div class="chart-title">
                    <i class="fas fa-money-bill"></i> Revenue Analytics
                </div>
                <canvas id="revenueChart"></canvas>
            </div>
        </div>
    </div>

    <!-- System Settings Tab -->
    <div class="tab-content" id="systemTab">
        <div class="table-container">
            <h3 style="margin-bottom: 20px;">System Configuration</h3>
            <form id="systemSettingsForm">
                <div class="form-group">
                    <label>Platform Fee (%)</label>
                    <input type="number" class="form-control" id="platformFee" value="20" min="0" max="100">
                </div>
                <div class="form-group">
                    <label>Session Timeout (minutes)</label>
                    <input type="number" class="form-control" id="sessionTimeout" value="10" min="1">
                </div>
                <div class="form-group">
                    <label>Max Free Sessions per Client</label>
                    <input type="number" class="form-control" id="maxFreeSessions" value="3" min="0">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="maintenanceMode"> Maintenance Mode
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="autoVerifyProfessionals"> Auto-verify Professionals
                    </label>
                </div>
                <button type="submit" class="btn-save">Save Settings</button>
            </form>
        </div>
    </div>
</div>

<!-- Edit User Modal -->
<div class="modal" id="editUserModal">
    <div class="modal-content">
        <div class="modal-header">
            <h3><i class="fas fa-user-edit"></i> Edit User</h3>
            <button class="modal-close" onclick="closeModal('editUserModal')">&times;</button>
        </div>
        <div class="modal-body">
            <form id="editUserForm">
                <input type="hidden" id="editUserId">
                <div class="form-row">
                    <div class="form-group">
                        <label>First Name</label>
                        <input type="text" class="form-control" id="editFirstName" required>
                    </div>
                    <div class="form-group">
                        <label>Last Name</label>
                        <input type="text" class="form-control" id="editLastName" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" class="form-control" id="editEmail" required>
                </div>
                <div class="form-group">
                    <label>Phone</label>
                    <input type="tel" class="form-control" id="editPhone">
                </div>
                <div class="form-group">
                    <label>Role</label>
                    <select class="form-control" id="editRole">
                        <option value="client">Client</option>
                        <option value="professional">Professional</option>
                        <option value="organization_admin">Organization Admin</option>
                        <option value="admin">Admin</option>
                        <option value="superadmin">Super Admin</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Status</label>
                    <select class="form-control" id="editStatus">
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Verified</label>
                    <select class="form-control" id="editVerified">
                        <option value="true">Verified</option>
                        <option value="false">Unverified</option>
                    </select>
                </div>
                <button type="submit" class="btn-save">Save Changes</button>
            </form>
        </div>
    </div>
</div>

<!-- Balance Modal -->
<div class="modal" id="balanceModal">
    <div class="modal-content">
        <div class="modal-header">
            <h3><i class="fas fa-coins"></i> Manage Balance</h3>
            <button class="modal-close" onclick="closeModal('balanceModal')">&times;</button>
        </div>
        <div class="modal-body">
            <form id="balanceForm">
                <input type="hidden" id="balanceUserId">
                <div class="form-group">
                    <label>Current Balance</label>
                    <input type="text" class="form-control" id="currentBalance" readonly>
                </div>
                <div class="form-group">
                    <label>Action</label>
                    <select class="form-control" id="balanceAction">
                        <option value="add">Add Credits</option>
                        <option value="deduct">Deduct Credits</option>
                        <option value="set">Set Exact Amount</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Amount</label>
                    <input type="number" class="form-control" id="balanceAmount" min="0" required>
                </div>
                <div class="form-group">
                    <label>Reason</label>
                    <input type="text" class="form-control" id="balanceReason" placeholder="e.g., Bonus, Refund, etc.">
                </div>
                <button type="submit" class="btn-save">Update Balance</button>
            </form>
        </div>
    </div>
</div>

<!-- Chat Modal -->
<div class="modal" id="chatModal">
    <div class="modal-content" style="max-width: 500px;">
        <div class="modal-header">
            <h3><i class="fas fa-comments"></i> Chat with <span id="chatUserName"></span></h3>
            <button class="modal-close" onclick="closeModal('chatModal')">&times;</button>
        </div>
        <div class="modal-body">
            <div style="height: 400px; overflow-y: auto; border: 1px solid #E5E7EB; border-radius: 10px; padding: 15px; margin-bottom: 15px;" id="chatMessages">
                <div class="message bot" style="display: flex; gap: 10px; margin-bottom: 15px;">
                    <div class="message-avatar" style="width: 35px; height: 35px; background: var(--primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content" style="background: #F3F4F6; padding: 10px 15px; border-radius: 15px; border-bottom-left-radius: 5px; max-width: 70%;">
                        <div>Hello! How can I help you today?</div>
                        <div style="font-size: 0.7rem; color: #999; margin-top: 5px;">Just now</div>
                    </div>
                </div>
            </div>
            <div style="display: flex; gap: 10px;">
                <input type="text" id="chatInput" class="form-control" placeholder="Type your message...">
                <button class="btn-save" style="width: auto; padding: 12px 25px;" onclick="sendChatMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Rate User Modal -->
<div class="modal" id="rateModal">
    <div class="modal-content">
        <div class="modal-header">
            <h3><i class="fas fa-star"></i> Rate User</h3>
            <button class="modal-close" onclick="closeModal('rateModal')">&times;</button>
        </div>
        <div class="modal-body">
            <form id="rateForm">
                <input type="hidden" id="rateUserId">
                <div class="form-group">
                    <label>Rating</label>
                    <div style="display: flex; gap: 10px; font-size: 2rem; color: #FFD700; justify-content: center; margin: 20px 0;">
                        <i class="far fa-star" onclick="setRating(1)" style="cursor: pointer;"></i>
                        <i class="far fa-star" onclick="setRating(2)" style="cursor: pointer;"></i>
                        <i class="far fa-star" onclick="setRating(3)" style="cursor: pointer;"></i>
                        <i class="far fa-star" onclick="setRating(4)" style="cursor: pointer;"></i>
                        <i class="far fa-star" onclick="setRating(5)" style="cursor: pointer;"></i>
                    </div>
                    <input type="hidden" id="ratingValue" value="0">
                </div>
                <div class="form-group">
                    <label>Comment</label>
                    <textarea class="form-control" id="ratingComment" rows="3" placeholder="Write your feedback..."></textarea>
                </div>
                <button type="submit" class="btn-save">Submit Rating</button>
            </form>
        </div>
    </div>
</div>

<!-- Reset Password Modal -->
<div class="modal" id="resetPasswordModal">
    <div class="modal-content">
        <div class="modal-header">
            <h3><i class="fas fa-key"></i> Reset Password</h3>
            <button class="modal-close" onclick="closeModal('resetPasswordModal')">&times;</button>
        </div>
        <div class="modal-body">
            <form id="resetPasswordForm">
                <input type="hidden" id="resetUserId">
                <div class="form-group">
                    <label>New Password</label>
                    <input type="password" class="form-control" id="newPassword" required minlength="8">
                </div>
                <div class="form-group">
                    <label>Confirm Password</label>
                    <input type="password" class="form-control" id="confirmPassword" required>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="forceLogout"> Force logout after password change
                    </label>
                </div>
                <button type="submit" class="btn-save">Reset Password</button>
            </form>
        </div>
    </div>
</div>

<script>
let users = [];
let professionals = [];
let organizations = [];
let clients = [];
let activities = [];
let currentRating = 0;
let userGrowthChart, userDistributionChart, sessionsChart, revenueChart;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    initCharts();
    initDataTables();
});

async function loadDashboardData() {
    try {
        const response = await fetch('/superadmin/api/dashboard/stats');
        const data = await response.json();
        
        // Update stats
        document.getElementById('totalUsers').textContent = data.stats.total_users;
        document.getElementById('totalProfessionals').textContent = data.stats.users_by_role.professional || 0;
        document.getElementById('totalOrganizations').textContent = data.stats.users_by_role.organization_admin || 0;
        document.getElementById('activeToday').textContent = data.stats.active_users;
        document.getElementById('totalRevenue').textContent = `KES ${data.stats.total_revenue || 0}`;
        
        users = data.users || [];
        activities = data.recent_activity || [];
        
        updateUsersTable();
        updateActivityFeed();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function initDataTables() {
    // Initialize DataTables if you want to use it
    // $('#usersTable').DataTable();
}

function updateUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>#${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td><span class="role-badge role-${user.role}">${user.role}</span></td>
            <td><span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
            <td><span class="status-badge ${user.is_verified ? 'status-active' : 'status-pending'}">${user.is_verified ? 'Verified' : 'Pending'}</span></td>
            <td>KES ${user.balance || 0}</td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn btn-view" onclick="viewUser(${user.id})" title="View"><i class="fas fa-eye"></i></button>
                    <button class="action-btn btn-edit" onclick="editUser(${user.id})" title="Edit"><i class="fas fa-edit"></i></button>
                    <button class="action-btn btn-impersonate" onclick="impersonateUser(${user.id})" title="Login as User"><i class="fas fa-mask"></i></button>
                    <button class="action-btn btn-reset" onclick="showResetPassword(${user.id})" title="Reset Password"><i class="fas fa-key"></i></button>
                    <button class="action-btn btn-balance" onclick="manageBalance(${user.id})" title="Balance"><i class="fas fa-coins"></i></button>
                    <button class="action-btn btn-chat" onclick="chatWithUser(${user.id}, '${user.name}')" title="Chat"><i class="fas fa-comments"></i></button>
                    <button class="action-btn btn-rate" onclick="rateUser(${user.id})" title="Rate"><i class="fas fa-star"></i></button>
                    <button class="action-btn btn-toggle" onclick="toggleUserStatus(${user.id})" title="Toggle Status"><i class="fas fa-power-off"></i></button>
                </div>
            </td>
        </tr>
    `).join('');
}

function updateActivityFeed() {
    const feed = document.getElementById('activityFeed');
    feed.innerHTML = activities.map(act => `
        <div class="activity-item">
            <div class="activity-icon activity-${act.action.toLowerCase()}">
                <i class="fas ${getActivityIcon(act.action)}"></i>
            </div>
            <div class="activity-details">
                <div class="activity-title">${act.description || act.action}</div>
                <div class="activity-time">${new Date(act.time).toLocaleString()} • IP: ${act.ip || 'Unknown'}</div>
            </div>
        </div>
    `).join('');
}

function getActivityIcon(action) {
    const icons = {
        'LOGIN': 'fa-sign-in-alt',
        'REGISTER': 'fa-user-plus',
        'PAYMENT': 'fa-credit-card',
        'SESSION': 'fa-video',
        'PROFILE_UPDATE': 'fa-user-edit',
        'PASSWORD_RESET': 'fa-key'
    };
    return icons[action] || 'fa-circle';
}

function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tab + 'Tab').classList.add('active');
}

// User Management Functions
async function editUser(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editFirstName').value = user.first_name;
    document.getElementById('editLastName').value = user.last_name;
    document.getElementById('editEmail').value = user.email;
    document.getElementById('editPhone').value = user.phone || '';
    document.getElementById('editRole').value = user.role;
    document.getElementById('editStatus').value = user.is_active;
    document.getElementById('editVerified').value = user.is_verified;
    
    openModal('editUserModal');
}

document.getElementById('editUserForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const userId = document.getElementById('editUserId').value;
    const data = {
        first_name: document.getElementById('editFirstName').value,
        last_name: document.getElementById('editLastName').value,
        email: document.getElementById('editEmail').value,
        phone: document.getElementById('editPhone').value,
        role: document.getElementById('editRole').value,
        is_active: document.getElementById('editStatus').value === 'true',
        is_verified: document.getElementById('editVerified').value === 'true'
    };
    
    try {
        const response = await fetch(`/superadmin/api/users/${userId}/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            Swal.fire('Success', 'User updated successfully', 'success');
            closeModal('editUserModal');
            loadDashboardData();
        } else {
            Swal.fire('Error', result.message, 'error');
        }
    } catch (error) {
        Swal.fire('Error', 'Failed to update user', 'error');
    }
});

async function viewUser(userId) {
    window.location.href = `/superadmin/users/${userId}`;
}

async function impersonateUser(userId) {
    const result = await Swal.fire({
        title: 'Impersonate User',
        text: 'You will be logged in as this user. Continue?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#667eea',
        cancelButtonColor: '#EF4444',
        confirmButtonText: 'Yes, impersonate'
    });
    
    if (result.isConfirmed) {
        try {
            const response = await fetch(`/superadmin/api/users/${userId}/impersonate`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                window.location.href = data.redirect;
            }
        } catch (error) {
            Swal.fire('Error', 'Failed to impersonate user', 'error');
        }
    }
}

function showResetPassword(userId) {
    document.getElementById('resetUserId').value = userId;
    openModal('resetPasswordModal');
}

document.getElementById('resetPasswordForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const password = document.getElementById('newPassword').value;
    const confirm = document.getElementById('confirmPassword').value;
    
    if (password !== confirm) {
        Swal.fire('Error', 'Passwords do not match', 'error');
        return;
    }
    
    const userId = document.getElementById('resetUserId').value;
    
    try {
        const response = await fetch(`/superadmin/api/users/${userId}/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        
        const result = await response.json();
        if (result.success) {
            Swal.fire('Success', 'Password reset successfully', 'success');
            closeModal('resetPasswordModal');
        } else {
            Swal.fire('Error', result.message, 'error');
        }
    } catch (error) {
        Swal.fire('Error', 'Failed to reset password', 'error');
    }
});

async function toggleUserStatus(userId) {
    const result = await Swal.fire({
        title: 'Toggle User Status',
        text: 'Are you sure you want to change this user\'s status?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#667eea',
        cancelButtonColor: '#EF4444',
        confirmButtonText: 'Yes, toggle'
    });
    
    if (result.isConfirmed) {
        try {
            const response = await fetch(`/superadmin/api/users/${userId}/toggle-status`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                Swal.fire('Success', `User ${data.is_active ? 'activated' : 'deactivated'}`, 'success');
                loadDashboardData();
            }
        } catch (error) {
            Swal.fire('Error', 'Failed to toggle status', 'error');
        }
    }
}

function manageBalance(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('balanceUserId').value = userId;
    document.getElementById('currentBalance').value = `KES ${user.balance || 0}`;
    openModal('balanceModal');
}

document.getElementById('balanceForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const userId = document.getElementById('balanceUserId').value;
    const action = document.getElementById('balanceAction').value;
    const amount = parseFloat(document.getElementById('balanceAmount').value);
    const reason = document.getElementById('balanceReason').value;
    
    try {
        const response = await fetch(`/superadmin/api/users/${userId}/balance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, amount, reason })
        });
        
        const result = await response.json();
        if (result.success) {
            Swal.fire('Success', 'Balance updated successfully', 'success');
            closeModal('balanceModal');
            loadDashboardData();
        } else {
            Swal.fire('Error', result.message, 'error');
        }
    } catch (error) {
        Swal.fire('Error', 'Failed to update balance', 'error');
    }
});

function chatWithUser(userId, userName) {
    document.getElementById('chatUserName').textContent = userName;
    openModal('chatModal');
    
    // Load chat history
    loadChatHistory(userId);
}

async function loadChatHistory(userId) {
    // Implement chat history loading
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '<div class="loading">Loading chat history...</div>';
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    
    // Add message to chat
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML += `
        <div class="message user" style="display: flex; gap: 10px; margin-bottom: 15px; justify-content: flex-end;">
            <div class="message-content" style="background: var(--primary); color: white; padding: 10px 15px; border-radius: 15px; border-bottom-right-radius: 5px; max-width: 70%;">
                <div>${escapeHtml(message)}</div>
                <div style="font-size: 0.7rem; color: rgba(255,255,255,0.7); margin-top: 5px;">Just now</div>
            </div>
            <div class="message-avatar" style="width: 35px; height: 35px; background: var(--primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;">
                <i class="fas fa-user"></i>
            </div>
        </div>
    `;
    
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Send to backend
    try {
        await fetch('/superadmin/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message })
        });
    } catch (error) {
        console.error('Failed to send message:', error);
    }
}

function rateUser(userId) {
    document.getElementById('rateUserId').value = userId;
    currentRating = 0;
    updateRatingStars();
    openModal('rateModal');
}

function setRating(rating) {
    currentRating = rating;
    document.getElementById('ratingValue').value = rating;
    updateRatingStars();
}

function updateRatingStars() {
    const stars = document.querySelectorAll('#rateModal .fa-star');
    stars.forEach((star, index) => {
        if (index < currentRating) {
            star.className = 'fas fa-star';
        } else {
            star.className = 'far fa-star';
        }
    });
}

document.getElementById('rateForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const userId = document.getElementById('rateUserId').value;
    const rating = document.getElementById('ratingValue').value;
    const comment = document.getElementById('ratingComment').value;
    
    if (rating === '0') {
        Swal.fire('Error', 'Please select a rating', 'error');
        return;
    }
    
    try {
        const response = await fetch('/superadmin/api/rate-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, rating, comment })
        });
        
        const result = await response.json();
        if (result.success) {
            Swal.fire('Success', 'Rating submitted successfully', 'success');
            closeModal('rateModal');
        } else {
            Swal.fire('Error', result.message, 'error');
        }
    } catch (error) {
        Swal.fire('Error', 'Failed to submit rating', 'error');
    }
});

// Modal Functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    document.body.style.overflow = '';
}

// Close modals when clicking outside
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Chart Initialization
function initCharts() {
    // User Growth Chart
    const userCtx = document.getElementById('userGrowthChart').getContext('2d');
    userGrowthChart = new Chart(userCtx, {
        type: 'line',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'New Users',
                data: [12, 19, 25, 30],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            }
        }
    });
    
    // User Distribution Chart
    const distCtx = document.getElementById('userDistributionChart').getContext('2d');
    userDistributionChart = new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['Clients', 'Professionals', 'Organizations', 'Admins'],
            datasets: [{
                data: [65, 20, 10, 5],
                backgroundColor: ['#667eea', '#10B981', '#F59E0B', '#EF4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// Search and Filter
document.getElementById('userSearch').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const filtered = users.filter(user => 
        user.name.toLowerCase().includes(searchTerm) ||
        user.email.toLowerCase().includes(searchTerm)
    );
    updateUsersTable(filtered);
});

document.getElementById('roleFilter').addEventListener('change', function() {
    filterUsers();
});

document.getElementById('statusFilter').addEventListener('change', function() {
    filterUsers();
});

function filterUsers() {
    const role = document.getElementById('roleFilter').value;
    const status = document.getElementById('statusFilter').value;
    
    let filtered = users;
    
    if (role) {
        filtered = filtered.filter(user => user.role === role);
    }
    
    if (status) {
        filtered = filtered.filter(user => 
            status === 'active' ? user.is_active : !user.is_active
        );
    }
    
    updateUsersTable(filtered);
}

// Utility function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
</script>
{% endblock %}
