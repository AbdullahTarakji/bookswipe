import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../widgets/responsive_container.dart';

/// Detailed analytics dashboard accessible from the admin panel.
class AnalyticsDashboardScreen extends ConsumerWidget {
  const AnalyticsDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(detailedAnalyticsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analytics Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(detailedAnalyticsProvider),
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
                onPressed: () => ref.invalidate(detailedAnalyticsProvider),
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (data) => _AnalyticsContent(data: data),
      ),
    );
  }
}

class _AnalyticsContent extends StatelessWidget {
  final Map<String, dynamic> data;

  const _AnalyticsContent({required this.data});

  @override
  Widget build(BuildContext context) {
    final engagement = data['engagement'] as Map<String, dynamic>? ?? {};
    final swipes = data['swipes'] as Map<String, dynamic>? ?? {};
    final popularBooks = data['popular_books'] as Map<String, dynamic>? ?? {};
    final retention = data['retention'] as Map<String, dynamic>? ?? {};
    final categories = data['categories'] as Map<String, dynamic>? ?? {};
    final isTablet = ResponsiveContainer.isTablet(context);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Engagement Section ──
        const _SectionHeader(title: 'User Engagement', icon: Icons.people),
        const SizedBox(height: 12),
        _EngagementCards(engagement: engagement),
        const SizedBox(height: 16),

        // ── Charts: side-by-side on tablet ──
        if (isTablet)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _SignupsChart(
                  signups: (engagement['signups_over_time'] as List<dynamic>?) ?? [],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _SwipesOverTimeChart(
                  swipes: (swipes['swipes_over_time'] as List<dynamic>?) ?? [],
                ),
              ),
            ],
          )
        else ...[
          _SignupsChart(
            signups: (engagement['signups_over_time'] as List<dynamic>?) ?? [],
          ),
          const SizedBox(height: 24),
          // ── Swipe Stats Section ──
          const _SectionHeader(title: 'Swipe Statistics', icon: Icons.swipe),
          const SizedBox(height: 12),
          _SwipeCards(swipes: swipes),
          const SizedBox(height: 16),
          _SwipesOverTimeChart(
            swipes: (swipes['swipes_over_time'] as List<dynamic>?) ?? [],
          ),
        ],

        if (isTablet) ...[
          const SizedBox(height: 24),
          const _SectionHeader(title: 'Swipe Statistics', icon: Icons.swipe),
          const SizedBox(height: 12),
          _SwipeCards(swipes: swipes),
        ],
        const SizedBox(height: 24),

        // ── Popular Books Section ──
        const _SectionHeader(title: 'Popular Books', icon: Icons.auto_awesome),
        const SizedBox(height: 12),
        if (isTablet)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _PopularBooksList(
                  title: 'Most Liked',
                  books: (popularBooks['most_liked'] as List<dynamic>?) ?? [],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _PopularBooksList(
                  title: 'Trending This Week',
                  books: (popularBooks['trending_this_week'] as List<dynamic>?) ?? [],
                ),
              ),
            ],
          )
        else ...[
          _PopularBooksList(
            title: 'Most Liked',
            books: (popularBooks['most_liked'] as List<dynamic>?) ?? [],
          ),
          const SizedBox(height: 12),
          _PopularBooksList(
            title: 'Trending This Week',
            books: (popularBooks['trending_this_week'] as List<dynamic>?) ?? [],
          ),
        ],
        const SizedBox(height: 24),

        // ── Retention Section ──
        const _SectionHeader(title: 'Retention', icon: Icons.repeat),
        const SizedBox(height: 12),
        _RetentionTable(
          cohorts: (retention['cohorts'] as List<dynamic>?) ?? [],
        ),
        const SizedBox(height: 24),

        // ── Category Breakdown ──
        const _SectionHeader(title: 'Category Breakdown', icon: Icons.category),
        const SizedBox(height: 12),
        _CategoryChart(
          categories: (categories['likes_by_category'] as List<dynamic>?) ?? [],
        ),
        const SizedBox(height: 32),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;

  const _SectionHeader({required this.title, required this.icon});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Icon(icon, size: 22, color: theme.colorScheme.primary),
        const SizedBox(width: 8),
        Text(title, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      ],
    );
  }
}

class _EngagementCards extends StatelessWidget {
  final Map<String, dynamic> engagement;

  const _EngagementCards({required this.engagement});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        _MetricCard(label: 'DAU', value: '${engagement['dau'] ?? 0}', icon: Icons.today, color: Colors.blue),
        _MetricCard(label: 'WAU', value: '${engagement['wau'] ?? 0}', icon: Icons.date_range, color: Colors.teal),
        _MetricCard(label: 'MAU', value: '${engagement['mau'] ?? 0}', icon: Icons.calendar_month, color: Colors.indigo),
      ],
    );
  }
}

class _SwipeCards extends StatelessWidget {
  final Map<String, dynamic> swipes;

  const _SwipeCards({required this.swipes});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        _MetricCard(label: 'Total Swipes', value: '${swipes['total_swipes'] ?? 0}', icon: Icons.swipe, color: Colors.deepPurple),
        _MetricCard(label: 'Like Ratio', value: '${swipes['like_ratio'] ?? 0}%', icon: Icons.favorite, color: Colors.pink),
        _MetricCard(label: 'Skip Ratio', value: '${swipes['skip_ratio'] ?? 0}%', icon: Icons.skip_next, color: Colors.orange),
        _MetricCard(label: 'Avg/User', value: '${swipes['swipes_per_user_avg'] ?? 0}', icon: Icons.person, color: Colors.green),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isTablet = ResponsiveContainer.isTablet(context);
    final width = (MediaQuery.of(context).size.width - (isTablet ? 56 : 44)) / (isTablet ? 3 : 2);

    return SizedBox(
      width: width,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(height: 8),
              Text(value, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(label, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ],
          ),
        ),
      ),
    );
  }
}

class _SignupsChart extends StatelessWidget {
  final List<dynamic> signups;

  const _SignupsChart({required this.signups});

  @override
  Widget build(BuildContext context) {
    if (signups.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final spots = <FlSpot>[];
    for (var i = 0; i < signups.length; i++) {
      spots.add(FlSpot(i.toDouble(), (signups[i]['count'] as num?)?.toDouble() ?? 0));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('New Signups (30 days)', style: theme.textTheme.bodyMedium),
            const SizedBox(height: 12),
            SizedBox(
              height: 180,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(
                    topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: Colors.blue,
                      barWidth: 3,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(show: true, color: Colors.blue.withValues(alpha: 0.15)),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SwipesOverTimeChart extends StatelessWidget {
  final List<dynamic> swipes;

  const _SwipesOverTimeChart({required this.swipes});

  @override
  Widget build(BuildContext context) {
    if (swipes.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final spots = <FlSpot>[];
    for (var i = 0; i < swipes.length; i++) {
      spots.add(FlSpot(i.toDouble(), (swipes[i]['count'] as num?)?.toDouble() ?? 0));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Swipes Over Time (30 days)', style: theme.textTheme.bodyMedium),
            const SizedBox(height: 12),
            SizedBox(
              height: 180,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(
                    topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: Colors.deepPurple,
                      barWidth: 3,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(show: true, color: Colors.deepPurple.withValues(alpha: 0.15)),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PopularBooksList extends StatelessWidget {
  final String title;
  final List<dynamic> books;

  const _PopularBooksList({required this.title, required this.books});

  @override
  Widget build(BuildContext context) {
    if (books.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            ...books.take(5).map((book) {
              final bookMap = book as Map<String, dynamic>;
              return ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: bookMap['thumbnail'] != null && (bookMap['thumbnail'] as String).isNotEmpty
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: Image.network(bookMap['thumbnail'] as String, width: 32, height: 48, fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => const Icon(Icons.book, size: 32)),
                      )
                    : const Icon(Icons.book, size: 32),
                title: Text(bookMap['title'] as String? ?? 'Unknown', maxLines: 1, overflow: TextOverflow.ellipsis),
                subtitle: Text(bookMap['authors'] as String? ?? '', maxLines: 1, overflow: TextOverflow.ellipsis),
                trailing: Chip(label: Text('${bookMap['like_count'] ?? 0}', style: theme.textTheme.bodySmall)),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _RetentionTable extends StatelessWidget {
  final List<dynamic> cohorts;

  const _RetentionTable({required this.cohorts});

  @override
  Widget build(BuildContext context) {
    if (cohorts.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Weekly Retention Cohorts', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            Table(
              columnWidths: const {
                0: FlexColumnWidth(2),
                1: FlexColumnWidth(1),
                2: FlexColumnWidth(1),
                3: FlexColumnWidth(1),
              },
              children: [
                TableRow(
                  children: ['Cohort', 'Size', 'W1 %', 'W2 %']
                      .map((h) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Text(h, style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold)),
                          ))
                      .toList(),
                ),
                ...cohorts.map((c) {
                  final cohort = c as Map<String, dynamic>;
                  return TableRow(
                    children: [
                      Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text(cohort['cohort_week'] as String? ?? '', style: theme.textTheme.bodySmall)),
                      Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text('${cohort['cohort_size'] ?? 0}', style: theme.textTheme.bodySmall)),
                      Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text('${cohort['retained_week_1'] ?? 0}%', style: theme.textTheme.bodySmall)),
                      Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Text('${cohort['retained_week_2'] ?? 0}%', style: theme.textTheme.bodySmall)),
                    ],
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryChart extends StatelessWidget {
  final List<dynamic> categories;

  const _CategoryChart({required this.categories});

  @override
  Widget build(BuildContext context) {
    if (categories.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final colors = [Colors.blue, Colors.red, Colors.green, Colors.orange, Colors.purple, Colors.teal, Colors.pink, Colors.amber, Colors.indigo, Colors.cyan];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Likes by Category', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  gridData: const FlGridData(show: false),
                  titlesData: FlTitlesData(
                    leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          final idx = value.toInt();
                          if (idx >= 0 && idx < categories.length) {
                            final name = (categories[idx] as Map)['category'] as String? ?? '';
                            return Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text(name.length > 6 ? '${name.substring(0, 5)}..' : name, style: theme.textTheme.bodySmall?.copyWith(fontSize: 10)),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: categories.asMap().entries.map((entry) {
                    final count = ((entry.value as Map)['count'] as num?)?.toDouble() ?? 0;
                    return BarChartGroupData(
                      x: entry.key,
                      barRods: [BarChartRodData(toY: count, color: colors[entry.key % colors.length], width: 16, borderRadius: const BorderRadius.vertical(top: Radius.circular(4)))],
                    );
                  }).toList(),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
