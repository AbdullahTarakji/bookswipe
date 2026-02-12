import 'dart:async';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

/// Handles Firebase Cloud Messaging setup, permission requests, and message routing.
class NotificationService {
  final FirebaseMessaging _messaging;

  /// Stream controller for foreground messages to be consumed by the UI.
  final StreamController<RemoteMessage> _foregroundController =
      StreamController<RemoteMessage>.broadcast();

  /// Stream of foreground notifications for UI consumption.
  Stream<RemoteMessage> get onForegroundMessage => _foregroundController.stream;

  /// Stream controller for notification taps (deep-link handling).
  final StreamController<RemoteMessage> _tapController =
      StreamController<RemoteMessage>.broadcast();

  /// Stream of notification tap events for deep-link navigation.
  Stream<RemoteMessage> get onNotificationTap => _tapController.stream;

  /// Creates a [NotificationService] with an optional [FirebaseMessaging] instance.
  NotificationService({FirebaseMessaging? messaging})
      : _messaging = messaging ?? FirebaseMessaging.instance;

  /// Request notification permission from the user.
  ///
  /// Returns true if the user granted permission.
  Future<bool> requestPermission() async {
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    return settings.authorizationStatus == AuthorizationStatus.authorized ||
        settings.authorizationStatus == AuthorizationStatus.provisional;
  }

  /// Get the current FCM device token.
  ///
  /// Returns null if the token is unavailable.
  Future<String?> getToken() async {
    try {
      return await _messaging.getToken();
    } catch (e) {
      debugPrint('Failed to get FCM token: $e');
      return null;
    }
  }

  /// Set up listeners for foreground messages, background taps, and token refresh.
  void setupMessageHandlers({
    void Function(String token)? onTokenRefresh,
  }) {
    // Foreground messages
    FirebaseMessaging.onMessage.listen((message) {
      _foregroundController.add(message);
    });

    // Notification tap (app was in background)
    FirebaseMessaging.onMessageOpenedApp.listen((message) {
      _tapController.add(message);
    });

    // Token refresh
    if (onTokenRefresh != null) {
      _messaging.onTokenRefresh.listen(onTokenRefresh);
    }
  }

  /// Check if a notification launched the app (cold start).
  ///
  /// Returns the initial message if the app was opened from a notification.
  Future<RemoteMessage?> getInitialMessage() async {
    return _messaging.getInitialMessage();
  }

  /// Clean up stream controllers.
  void dispose() {
    _foregroundController.close();
    _tapController.close();
  }
}
