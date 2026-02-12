import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../services/api_service.dart';

class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  ConsumerState<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  bool _isLoading = false;

  Future<void> _handleUpgrade() async {
    setState(() => _isLoading = true);
    try {
      final api = ref.read(apiServiceProvider);
      final checkoutUrl = await api.createCheckoutSession();
      if (!mounted) return;
      // Show a dialog with the checkout URL since we can't do in-app browser easily
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Complete Payment'),
          content: Text(
            'Visit this URL to complete your subscription:\n\n$checkoutUrl',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Done'),
            ),
          ],
        ),
      );
      // Refresh subscription status after returning
      await ref.read(authStateProvider.notifier).refreshSubscription();
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ApiService.formatError(e))),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleCancel() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Subscription?'),
        content: const Text(
          'Your Premium access will continue until the end of your billing period.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Keep'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Cancel Subscription'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _isLoading = true);
    try {
      final api = ref.read(apiServiceProvider);
      await api.cancelSubscription();
      if (!mounted) return;
      await ref.read(authStateProvider.notifier).refreshSubscription();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Subscription cancelled')),
      );
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ApiService.formatError(e))),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleManageBilling() async {
    setState(() => _isLoading = true);
    try {
      final api = ref.read(apiServiceProvider);
      final portalUrl = await api.createBillingPortalSession();
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Billing Portal'),
          content: Text(
            'Visit this URL to manage your billing:\n\n$portalUrl',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Done'),
            ),
          ],
        ),
      );
    } on DioException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ApiService.formatError(e))),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final user = authState.valueOrNull;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Subscription')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Current plan card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Icon(
                    user?.isPremium == true ? Icons.workspace_premium : Icons.star_outline,
                    size: 48,
                    color: user?.isPremium == true
                        ? Colors.amber
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    user?.isPremium == true ? 'Premium' : 'Free Plan',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.isPremium == true
                        ? 'You have unlimited swipes!'
                        : '10 swipes per day',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          if (user?.isPremium != true) ...[
            // Premium upgrade card
            Card(
              color: theme.colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.workspace_premium, color: Colors.amber),
                        const SizedBox(width: 8),
                        Text(
                          'Premium',
                          style: theme.textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '\$4.99/mo',
                          style: theme.textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _buildFeatureRow(Icons.all_inclusive, 'Unlimited swipes'),
                    const SizedBox(height: 8),
                    _buildFeatureRow(Icons.category, 'All categories'),
                    const SizedBox(height: 8),
                    _buildFeatureRow(Icons.support_agent, 'Priority support'),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _isLoading ? null : _handleUpgrade,
                        child: _isLoading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Text('Upgrade to Premium'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ] else ...[
            // Manage subscription
            Card(
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.receipt_long),
                    title: const Text('Manage Billing'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: _isLoading ? null : _handleManageBilling,
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: Icon(Icons.cancel, color: theme.colorScheme.error),
                    title: Text(
                      'Cancel Subscription',
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: _isLoading ? null : _handleCancel,
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFeatureRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.green),
        const SizedBox(width: 8),
        Text(text),
      ],
    );
  }
}
