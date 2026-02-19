import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../providers/providers.dart';
import '../widgets/responsive_container.dart';

class PrivacySettingsScreen extends ConsumerStatefulWidget {
  const PrivacySettingsScreen({super.key});

  @override
  ConsumerState<PrivacySettingsScreen> createState() => _PrivacySettingsScreenState();
}

class _PrivacySettingsScreenState extends ConsumerState<PrivacySettingsScreen> {
  bool _analyticsConsent = false;
  bool _marketingConsent = false;
  bool _loading = true;
  bool _exporting = false;

  @override
  void initState() {
    super.initState();
    _loadConsent();
  }

  Future<void> _loadConsent() async {
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.getPrivacyConsent();
      setState(() {
        _analyticsConsent = data['analytics_consent'] as bool? ?? false;
        _marketingConsent = data['marketing_consent'] as bool? ?? false;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _saveConsent() async {
    try {
      final api = ref.read(apiServiceProvider);
      await api.updatePrivacyConsent(
        analyticsConsent: _analyticsConsent,
        marketingConsent: _marketingConsent,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Privacy preferences saved')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save preferences')),
        );
      }
    }
  }

  Future<void> _exportData() async {
    setState(() => _exporting = true);
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.exportMyData();
      final jsonStr = const JsonEncoder.withIndent('  ').convert(data);

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/bookswipe_data_export.json');
      await file.writeAsString(jsonStr);

      await Share.shareXFiles([XFile(file.path)], text: 'BookSwipe Data Export');
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to export data')),
        );
      }
    } finally {
      setState(() => _exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Privacy Settings')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ResponsiveContainer(
              maxWidth: 700,
              child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Data & Consent', style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                SwitchListTile(
                  title: const Text('Analytics'),
                  subtitle: const Text('Share anonymous usage data to help improve BookSwipe'),
                  value: _analyticsConsent,
                  onChanged: (v) {
                    setState(() => _analyticsConsent = v);
                    _saveConsent();
                  },
                ),
                SwitchListTile(
                  title: const Text('Marketing Communications'),
                  subtitle: const Text('Receive book recommendations and feature updates'),
                  value: _marketingConsent,
                  onChanged: (v) {
                    setState(() => _marketingConsent = v);
                    _saveConsent();
                  },
                ),
                const Divider(height: 32),
                Text('Your Data', style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                ListTile(
                  leading: const Icon(Icons.download),
                  title: const Text('Export My Data'),
                  subtitle: const Text('Download all your data as JSON (GDPR)'),
                  trailing: _exporting
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.chevron_right),
                  onTap: _exporting ? null : _exportData,
                ),
              ],
            ),
            ),
    );
  }
}
