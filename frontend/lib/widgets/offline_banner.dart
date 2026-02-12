import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Provider that periodically checks connectivity by pinging the backend.
final connectivityProvider =
    StateNotifierProvider<ConnectivityNotifier, bool>((ref) {
  return ConnectivityNotifier();
});

/// Notifier that tracks online/offline status by pinging the health endpoint.
class ConnectivityNotifier extends StateNotifier<bool> {
  Timer? _timer;
  final Dio _dio = Dio(BaseOptions(
    baseUrl: const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://localhost:8000',
    ),
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  ));

  /// Starts as online (true).
  ConnectivityNotifier() : super(true) {
    _startChecking();
  }

  void _startChecking() {
    // Check immediately, then every 30 seconds
    _check();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _check());
  }

  Future<void> _check() async {
    try {
      await _dio.get('/health');
      if (!state) state = true;
    } catch (_) {
      if (state) state = false;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _dio.close();
    super.dispose();
  }
}

/// A banner that slides in from the top when the app is offline.
class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(connectivityProvider);

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: isOnline
          ? const SizedBox.shrink()
          : Container(
              key: const ValueKey('offline'),
              width: double.infinity,
              color: Theme.of(context).colorScheme.error,
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.cloud_off, color: Colors.white, size: 16),
                  SizedBox(width: 8),
                  Text(
                    'No internet connection',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
