import 'dart:io' show Platform;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

import '../providers/providers.dart';
import '../providers/subscription_provider.dart';
import '../services/api_service.dart';
import '../services/revenuecat_service.dart';

class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  ConsumerState<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  bool _isLoading = false;

  /// Whether the current platform uses RevenueCat (mobile) or Stripe (web).
  bool get _isMobile => isRevenueCatSupported;

  @override
  void initState() {
    super.initState();
    if (_isMobile) {
      // Ensure offerings are loaded
      Future.microtask(() => ref.read(subscriptionProvider.notifier).refresh());
    }
  }

  // ── Mobile: RevenueCat purchase ────────────────────────────

  Future<void> _handleMobilePurchase(Package package) async {
    setState(() => _isLoading = true);
    try {
      final success = await ref.read(subscriptionProvider.notifier).purchase(package);
      if (!mounted) return;
      if (success) {
        // Also refresh backend-side auth state
        await ref.read(authStateProvider.notifier).refreshSubscription();
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Welcome to Premium! 🎉')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Purchase failed: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleRestore() async {
    setState(() => _isLoading = true);
    try {
      await ref.read(subscriptionProvider.notifier).restore();
      if (!mounted) return;
      final sub = ref.read(subscriptionProvider);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(sub.isPremium
              ? 'Purchases restored! Premium is active.'
              : 'No previous purchases found.'),
        ),
      );
      if (sub.isPremium) {
        await ref.read(authStateProvider.notifier).refreshSubscription();
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Restore failed: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ── Web: Stripe checkout ──────────────────────────────────

  Future<void> _handleWebUpgrade() async {
    setState(() => _isLoading = true);
    try {
      final api = ref.read(apiServiceProvider);
      final checkoutUrl = await api.createCheckoutSession();
      if (!mounted) return;
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

  // ── Shared: cancel (web/Stripe only) ──────────────────────

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
    if (_isMobile) {
      // Open platform-native subscription management
      final url = Platform.isIOS
          ? 'https://apps.apple.com/account/subscriptions'
          : 'https://play.google.com/store/account/subscriptions';
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      return;
    }

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

  // ── Build ─────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final user = authState.valueOrNull;
    final theme = Theme.of(context);
    final sub = ref.watch(subscriptionProvider);
    final isPremium = user?.isPremium == true || sub.isPremium;

    return Scaffold(
      appBar: AppBar(title: const Text('Subscription')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Current plan card
          _buildCurrentPlanCard(theme, isPremium),
          const SizedBox(height: 24),

          if (!isPremium) ...[
            if (_isMobile)
              _buildMobilePaywall(theme, sub)
            else
              _buildWebUpgradeCard(theme),
          ] else ...[
            // Manage subscription
            _buildManageCard(theme),
          ],

          const SizedBox(height: 24),

          // Restore purchases (mobile only, always visible)
          if (_isMobile) ...[
            OutlinedButton.icon(
              onPressed: _isLoading ? null : _handleRestore,
              icon: const Icon(Icons.restore),
              label: const Text('Restore Purchases'),
            ),
            const SizedBox(height: 16),
          ],

          // Legal links
          _buildLegalLinks(theme),
        ],
      ),
    );
  }

  Widget _buildCurrentPlanCard(ThemeData theme, bool isPremium) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Icon(
              isPremium ? Icons.workspace_premium : Icons.star_outline,
              size: 48,
              color: isPremium ? Colors.amber : theme.colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 12),
            Text(
              isPremium ? 'Premium' : 'Free Plan',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              isPremium ? 'You have unlimited swipes!' : '10 swipes per day',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMobilePaywall(ThemeData theme, SubscriptionState sub) {
    final offerings = sub.offerings;
    final currentOffering = offerings?.current;

    if (sub.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (currentOffering == null || currentOffering.availablePackages.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            'No subscription plans available at this time.',
            style: theme.textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return Column(
      children: [
        for (final package in currentOffering.availablePackages)
          _buildPackageCard(theme, package),
      ],
    );
  }

  Widget _buildPackageCard(ThemeData theme, Package package) {
    final product = package.storeProduct;
    return Card(
      color: theme.colorScheme.primaryContainer,
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.workspace_premium, color: Colors.amber),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    product.title,
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Text(
                  product.priceString,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.primary,
                  ),
                ),
              ],
            ),
            if (product.description.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                product.description,
                style: theme.textTheme.bodyMedium,
              ),
            ],
            const SizedBox(height: 12),
            _buildFeatureRow(Icons.all_inclusive, 'Unlimited swipes'),
            const SizedBox(height: 8),
            _buildFeatureRow(Icons.category, 'All categories'),
            const SizedBox(height: 8),
            _buildFeatureRow(Icons.support_agent, 'Priority support'),
            const SizedBox(height: 16),
            // Subscription terms
            Text(
              _subscriptionTerms(product),
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _isLoading ? null : () => _handleMobilePurchase(package),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text('Subscribe for ${product.priceString}'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _subscriptionTerms(StoreProduct product) {
    return 'Subscription automatically renews at ${product.priceString} '
        'unless cancelled at least 24 hours before the end of the current period. '
        'You can manage or cancel your subscription in your '
        '${!kIsWeb && Platform.isIOS ? "Apple ID" : "Google Play"} settings.';
  }

  Widget _buildWebUpgradeCard(ThemeData theme) {
    return Card(
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
                onPressed: _isLoading ? null : _handleWebUpgrade,
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
    );
  }

  Widget _buildManageCard(ThemeData theme) {
    return Card(
      child: Column(
        children: [
          ListTile(
            leading: const Icon(Icons.receipt_long),
            title: const Text('Manage Billing'),
            subtitle: Text(_isMobile
                ? 'Manage in ${!kIsWeb && Platform.isIOS ? "App Store" : "Google Play"}'
                : 'Stripe billing portal'),
            trailing: const Icon(Icons.chevron_right),
            onTap: _isLoading ? null : _handleManageBilling,
          ),
          if (!_isMobile) ...[
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
        ],
      ),
    );
  }

  Widget _buildLegalLinks(ThemeData theme) {
    return Column(
      children: [
        TextButton(
          onPressed: () => launchUrl(
            Uri.parse('https://bookswipe.app/terms'),
            mode: LaunchMode.externalApplication,
          ),
          child: const Text('Terms of Service'),
        ),
        TextButton(
          onPressed: () => launchUrl(
            Uri.parse('https://bookswipe.app/privacy'),
            mode: LaunchMode.externalApplication,
          ),
          child: const Text('Privacy Policy'),
        ),
      ],
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
