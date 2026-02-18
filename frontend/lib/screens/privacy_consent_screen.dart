import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/providers.dart';

/// Key used to track whether the user has seen the consent screen.
const _consentShownKey = 'privacy_consent_shown';

/// Check if consent screen needs to be shown.
Future<bool> shouldShowConsentScreen() async {
  final prefs = await SharedPreferences.getInstance();
  return !(prefs.getBool(_consentShownKey) ?? false);
}

/// Mark consent screen as shown.
Future<void> markConsentShown() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setBool(_consentShownKey, true);
}

class PrivacyConsentScreen extends ConsumerStatefulWidget {
  const PrivacyConsentScreen({super.key});

  @override
  ConsumerState<PrivacyConsentScreen> createState() => _PrivacyConsentScreenState();
}

class _PrivacyConsentScreenState extends ConsumerState<PrivacyConsentScreen> {
  bool _analyticsConsent = false;
  bool _marketingConsent = false;
  bool _saving = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),
              Icon(Icons.privacy_tip_outlined, size: 48, color: theme.colorScheme.primary),
              const SizedBox(height: 16),
              Text('Your Privacy Matters', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Text(
                'We respect your privacy. Please choose which data processing you consent to. '
                'You can change these settings at any time in Settings > Privacy.',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              SwitchListTile(
                title: const Text('Analytics'),
                subtitle: const Text('Help us improve BookSwipe by sharing anonymous usage data'),
                value: _analyticsConsent,
                onChanged: (v) => setState(() => _analyticsConsent = v),
              ),
              const Divider(),
              SwitchListTile(
                title: const Text('Marketing Communications'),
                subtitle: const Text('Receive book recommendations and feature updates via email'),
                value: _marketingConsent,
                onChanged: (v) => setState(() => _marketingConsent = v),
              ),
              const Spacer(),
              Text(
                'By continuing, you agree to our Privacy Policy and Terms of Service.',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _saving ? null : _acceptAndContinue,
                  child: _saving
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Continue'),
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: _saving ? null : _declineAndContinue,
                  child: const Text('Continue without optional consent'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _acceptAndContinue() async {
    setState(() => _saving = true);
    try {
      final api = ref.read(apiServiceProvider);
      await api.updatePrivacyConsent(
        analyticsConsent: _analyticsConsent,
        marketingConsent: _marketingConsent,
      );
    } catch (_) {
      // Best effort — store locally even if backend call fails
    }
    await markConsentShown();
    if (mounted) context.go('/');
  }

  Future<void> _declineAndContinue() async {
    setState(() => _saving = true);
    try {
      final api = ref.read(apiServiceProvider);
      await api.updatePrivacyConsent(analyticsConsent: false, marketingConsent: false);
    } catch (_) {}
    await markConsentShown();
    if (mounted) context.go('/');
  }
}
