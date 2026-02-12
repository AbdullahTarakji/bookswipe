import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/notification.dart';
import '../services/api_service.dart';
import 'providers.dart';

// --- Notification Preferences ---

/// Provides the current user's notification preferences.
final notificationPreferencesProvider =
    AsyncNotifierProvider<NotificationPreferencesNotifier, NotificationPreferences>(
  NotificationPreferencesNotifier.new,
);

/// Notifier that manages notification preference state and updates.
class NotificationPreferencesNotifier extends AsyncNotifier<NotificationPreferences> {
  @override
  Future<NotificationPreferences> build() async {
    final auth = ref.watch(authStateProvider);
    if (auth.valueOrNull == null) return const NotificationPreferences();
    final api = ref.read(apiServiceProvider);
    try {
      final data = await api.getNotificationPreferences();
      return NotificationPreferences.fromJson(data);
    } on DioException catch (e) {
      throw ApiService.formatError(e);
    }
  }

  /// Update a single preference and persist to the server.
  Future<void> updatePreference({
    bool? recommendations,
    bool? social,
    bool? marketing,
  }) async {
    final api = ref.read(apiServiceProvider);
    try {
      final data = await api.updateNotificationPreferences(
        recommendations: recommendations,
        social: social,
        marketing: marketing,
      );
      state = AsyncValue.data(NotificationPreferences.fromJson(data));
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    }
  }
}

// --- Notification History ---

/// Provides the notification history/inbox for the current user.
final notificationHistoryProvider =
    AsyncNotifierProvider<NotificationHistoryNotifier, NotificationHistoryState>(
  NotificationHistoryNotifier.new,
);

/// State for the notification history including pagination and unread count.
class NotificationHistoryState {
  final List<AppNotification> notifications;
  final int total;
  final int unreadCount;
  final int page;

  const NotificationHistoryState({
    this.notifications = const [],
    this.total = 0,
    this.unreadCount = 0,
    this.page = 1,
  });
}

/// Notifier that manages notification history with pagination and read status.
class NotificationHistoryNotifier extends AsyncNotifier<NotificationHistoryState> {
  @override
  Future<NotificationHistoryState> build() async {
    final auth = ref.watch(authStateProvider);
    if (auth.valueOrNull == null) return const NotificationHistoryState();
    return _fetch(1);
  }

  Future<NotificationHistoryState> _fetch(int page) async {
    final api = ref.read(apiServiceProvider);
    final data = await api.getNotificationHistory(page: page);
    final items = (data['notifications'] as List<dynamic>)
        .map((n) => AppNotification.fromJson(n as Map<String, dynamic>))
        .toList();
    return NotificationHistoryState(
      notifications: items,
      total: data['total'] as int? ?? 0,
      unreadCount: data['unread_count'] as int? ?? 0,
      page: page,
    );
  }

  /// Refresh the notification list.
  Future<void> refresh() async {
    state = const AsyncValue.loading();
    try {
      state = AsyncValue.data(await _fetch(1));
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    }
  }

  /// Load a specific page.
  Future<void> loadPage(int page) async {
    state = const AsyncValue.loading();
    try {
      state = AsyncValue.data(await _fetch(page));
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    }
  }

  /// Mark a single notification as read (optimistic update).
  Future<void> markAsRead(int notificationId) async {
    final api = ref.read(apiServiceProvider);
    final current = state.valueOrNull;
    if (current == null) return;

    // Optimistic update
    final updated = current.notifications.map((n) {
      return n.id == notificationId ? n.copyWith(isRead: true) : n;
    }).toList();
    final wasUnread = current.notifications.any((n) => n.id == notificationId && !n.isRead);
    state = AsyncValue.data(NotificationHistoryState(
      notifications: updated,
      total: current.total,
      unreadCount: wasUnread ? current.unreadCount - 1 : current.unreadCount,
      page: current.page,
    ));

    try {
      await api.markNotificationRead(notificationId);
    } catch (_) {
      // Revert on failure
      state = AsyncValue.data(current);
    }
  }

  /// Mark all notifications as read.
  Future<void> markAllAsRead() async {
    final api = ref.read(apiServiceProvider);
    final current = state.valueOrNull;
    if (current == null) return;

    final updated = current.notifications.map((n) => n.copyWith(isRead: true)).toList();
    state = AsyncValue.data(NotificationHistoryState(
      notifications: updated,
      total: current.total,
      unreadCount: 0,
      page: current.page,
    ));

    try {
      await api.markAllNotificationsRead();
    } catch (_) {
      state = AsyncValue.data(current);
    }
  }
}

/// Provides just the unread notification count for badge display.
final unreadNotificationCountProvider = Provider<int>((ref) {
  final history = ref.watch(notificationHistoryProvider);
  return history.valueOrNull?.unreadCount ?? 0;
});
