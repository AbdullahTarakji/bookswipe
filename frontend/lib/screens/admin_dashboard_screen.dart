import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/providers.dart';

class AdminDashboardScreen extends ConsumerWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(adminAnalyticsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => context.push('/admin/system'),
            tooltip: 'System Info',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(adminAnalyticsProvider),
          ),
        ],
      ),
      body: analyticsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
              const SizedBox(height: 16),
              Text('Failed to load analytics', style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(error.toString(), style: theme.textTheme.bodySmall),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: () => ref.invalidate(adminAnalyticsProvider),
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (analytics) => _DashboardContent(analytics: analytics),
      ),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  final Map<String, dynamic> analytics;

  const _DashboardContent({required this.analytics});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final totalUsers = analytics['total_users'] as int? ?? 0;
    final activeUsers = analytics['active_users_7d'] as int? ?? 0;
    final bannedUsers = analytics['banned_users'] as int? ?? 0;
    final totalLikes = analytics['total_likes'] as int? ?? 0;
    final totalSkips = analytics['total_skips'] as int? ?? 0;
    final adminUsers = analytics['admin_users'] as int? ?? 0;
    final userGrowth = (analytics['user_growth'] as List<dynamic>?) ?? [];
    final popularCategories = (analytics['popular_categories'] as List<dynamic>?) ?? [];
    final recentUsers = (analytics['recent_users'] as List<dynamic>?) ?? [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Quick actions
        Row(
          children: [
            Expanded(
              child: FilledButton.icon(
                onPressed: () => GoRouter.of(context).push('/admin/users'),
                icon: const Icon(Icons.people),
                label: const Text('Manage Users'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => GoRouter.of(context).push('/admin/system'),
                icon: const Icon(Icons.settings),
                label: const Text('System Info'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: FilledButton.tonalIcon(
            onPressed: () => GoRouter.of(context).push('/admin/analytics'),
            icon: const Icon(Icons.analytics),
            label: const Text('Detailed Analytics'),
          ),
        ),
        const SizedBox(height: 24),

        // Stats cards
        _buildStatsRow(theme, totalUsers, activeUsers, bannedUsers, totalLikes, totalSkips, adminUsers),
        const SizedBox(height: 24),

        // User growth chart
        if (userGrowth.isNotEmpty) ...[
          Text('User Growth (30 days)', style: theme.textTheme.titleMedium),
          const SizedBox(height: 12),
          SizedBox(
            height: 200,
            child: _UserGrowthChart(data: userGrowth),
          ),
          const SizedBox(height: 24),
        ],

        // Popular categories chart
        if (popularCategories.isNotEmpty) ...[
          Text('Popular Categories', style: theme.textTheme.titleMedium),
          const SizedBox(height: 12),
          SizedBox(
            height: 200,
            child: _CategoriesChart(data: popularCategories),
          ),
          const SizedBox(height: 24),
        ],

        // Recent users
        if (recentUsers.isNotEmpty) ...[
          Text('Recent Users', style: theme.textTheme.titleMedium),
          const SizedBox(height: 12),
          ...recentUsers.map((u) => _RecentUserCard(user: u)),
        ],
      ],
    );
  }

  Widget _buildStatsRow(ThemeData theme, int total, int active, int banned,
      int likes, int skips, int admins) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        _StatCard(
          icon: Icons.people,
          label: 'Total Users',
          value: '$total',
          color: theme.colorScheme.primary,
        ),
        _StatCard(
          icon: Icons.trending_up,
          label: 'Active (7d)',
          value: '$active',
          color: Colors.green,
        ),
        _StatCard(
          icon: Icons.block,
          label: 'Banned',
          value: '$banned',
          color: Colors.red,
        ),
        _StatCard(
          icon: Icons.favorite,
          label: 'Total Likes',
          value: '$likes',
          color: Colors.pink,
        ),
        _StatCard(
          icon: Icons.skip_next,
          label: 'Total Skips',
          value: '$skips',
          color: Colors.orange,
        ),
        _StatCard(
          icon: Icons.admin_panel_settings,
          label: 'Admins',
          value: '$admins',
          color: Colors.purple,
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final width = (MediaQuery.of(context).size.width - 44) / 2;

    return SizedBox(
      width: width,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 8),
              Text(
                value,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                label,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _UserGrowthChart extends StatelessWidget {
  final List<dynamic> data;

  const _UserGrowthChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final spots = <FlSpot>[];
    for (var i = 0; i < data.length; i++) {
      final count = (data[i]['count'] as num?)?.toDouble() ?? 0;
      spots.add(FlSpot(i.toDouble(), count));
    }

    if (spots.isEmpty) {
      return const Center(child: Text('No data'));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: LineChart(
          LineChartData(
            gridData: const FlGridData(show: false),
            titlesData: FlTitlesData(
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 32,
                  getTitlesWidget: (value, meta) {
                    return Text(
                      value.toInt().toString(),
                      style: theme.textTheme.bodySmall,
                    );
                  },
                ),
              ),
              bottomTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
              topTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
              rightTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
            ),
            borderData: FlBorderData(show: false),
            lineBarsData: [
              LineChartBarData(
                spots: spots,
                isCurved: true,
                color: theme.colorScheme.primary,
                barWidth: 3,
                dotData: const FlDotData(show: false),
                belowBarData: BarAreaData(
                  show: true,
                  color: theme.colorScheme.primary.withValues(alpha: 0.15),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CategoriesChart extends StatelessWidget {
  final List<dynamic> data;

  const _CategoriesChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = [
      Colors.blue,
      Colors.red,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.pink,
      Colors.amber,
      Colors.indigo,
      Colors.cyan,
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: BarChart(
          BarChartData(
            alignment: BarChartAlignment.spaceAround,
            gridData: const FlGridData(show: false),
            titlesData: FlTitlesData(
              leftTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  getTitlesWidget: (value, meta) {
                    final index = value.toInt();
                    if (index >= 0 && index < data.length) {
                      final name = data[index]['name'] as String? ?? '';
                      return Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          name.length > 6 ? '${name.substring(0, 5)}..' : name,
                          style: theme.textTheme.bodySmall?.copyWith(fontSize: 10),
                        ),
                      );
                    }
                    return const SizedBox.shrink();
                  },
                ),
              ),
              topTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
              rightTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
            ),
            borderData: FlBorderData(show: false),
            barGroups: data.asMap().entries.map((entry) {
              final count = (entry.value['count'] as num?)?.toDouble() ?? 0;
              return BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: count,
                    color: colors[entry.key % colors.length],
                    width: 16,
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                  ),
                ],
              );
            }).toList(),
          ),
        ),
      ),
    );
  }
}

class _RecentUserCard extends StatelessWidget {
  final dynamic user;

  const _RecentUserCard({required this.user});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final email = user['email'] as String? ?? '';
    final role = user['role'] as String? ?? 'user';
    final isBanned = user['is_banned'] as bool? ?? false;
    final createdAt = user['created_at'] as String? ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: role == 'admin'
              ? Colors.purple.withValues(alpha: 0.2)
              : theme.colorScheme.primaryContainer,
          child: Icon(
            role == 'admin' ? Icons.admin_panel_settings : Icons.person,
            color: role == 'admin' ? Colors.purple : theme.colorScheme.onPrimaryContainer,
          ),
        ),
        title: Text(email, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(
          createdAt.isNotEmpty ? createdAt.substring(0, 10) : '',
          style: theme.textTheme.bodySmall,
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isBanned)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Banned',
                  style: theme.textTheme.bodySmall?.copyWith(color: Colors.red),
                ),
              ),
            if (role == 'admin')
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.purple.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Admin',
                  style: theme.textTheme.bodySmall?.copyWith(color: Colors.purple),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
