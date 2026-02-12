import 'package:bookswipe/models/notification.dart';
import 'package:bookswipe/providers/notification_providers.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/notification_inbox_screen.dart';
import 'package:bookswipe/screens/notification_preferences_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

class MockAuthService extends Mock implements AuthService {}

void main() {
  group('NotificationPreferences model', () {
    test('fromJson parses preferences', () {
      final json = {
        'recommendations': true,
        'social': false,
        'marketing': true,
      };
      final prefs = NotificationPreferences.fromJson(json);
      expect(prefs.recommendations, true);
      expect(prefs.social, false);
      expect(prefs.marketing, true);
    });

    test('defaults when fields missing', () {
      final prefs = NotificationPreferences.fromJson({});
      expect(prefs.recommendations, true);
      expect(prefs.social, true);
      expect(prefs.marketing, false);
    });

    test('copyWith creates modified copy', () {
      const prefs = NotificationPreferences(
        recommendations: true,
        social: true,
        marketing: false,
      );
      final updated = prefs.copyWith(marketing: true);
      expect(updated.marketing, true);
      expect(updated.recommendations, true);
      expect(prefs.marketing, false);
    });
  });

  group('AppNotification model', () {
    test('fromJson parses notification', () {
      final json = {
        'id': 1,
        'title': 'Test Title',
        'body': 'Test body text',
        'category': 'recommendations',
        'deep_link': '/book/123',
        'is_read': false,
        'created_at': '2026-02-13T10:00:00',
      };
      final notif = AppNotification.fromJson(json);
      expect(notif.id, 1);
      expect(notif.title, 'Test Title');
      expect(notif.body, 'Test body text');
      expect(notif.category, 'recommendations');
      expect(notif.deepLink, '/book/123');
      expect(notif.isRead, false);
    });

    test('fromJson defaults category to general', () {
      final json = {
        'id': 2,
        'title': 'Title',
        'body': 'Body',
        'created_at': '2026-01-01T00:00:00',
      };
      final notif = AppNotification.fromJson(json);
      expect(notif.category, 'general');
      expect(notif.deepLink, isNull);
      expect(notif.isRead, false);
    });

    test('copyWith updates isRead', () {
      final notif = AppNotification(
        id: 1,
        title: 'Title',
        body: 'Body',
        createdAt: DateTime(2026, 1, 1),
      );
      final read = notif.copyWith(isRead: true);
      expect(read.isRead, true);
      expect(notif.isRead, false);
    });
  });

  group('NotificationPreferencesScreen', () {
    testWidgets('shows preferences with toggles', (tester) async {
      final mockApi = MockApiService();
      final mockAuth = MockAuthService();
      when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(mockApi),
            authServiceProvider.overrideWithValue(mockAuth),
            notificationPreferencesProvider.overrideWith(
              () => _StaticPrefsNotifier(const NotificationPreferences(
                recommendations: true,
                social: true,
                marketing: false,
              )),
            ),
          ],
          child: const MaterialApp(home: NotificationPreferencesScreen()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Recommendations'), findsOneWidget);
      expect(find.text('Social'), findsOneWidget);
      expect(find.text('Marketing'), findsOneWidget);
      expect(find.byType(SwitchListTile), findsNWidgets(3));
      expect(find.text('Notification Settings'), findsOneWidget);
    });
  });

  group('NotificationInboxScreen', () {
    testWidgets('shows empty state', (tester) async {
      final mockApi = MockApiService();
      final mockAuth = MockAuthService();
      when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(mockApi),
            authServiceProvider.overrideWithValue(mockAuth),
            notificationHistoryProvider.overrideWith(
              () => _StaticHistoryNotifier(const NotificationHistoryState()),
            ),
          ],
          child: const MaterialApp(home: NotificationInboxScreen()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('No notifications yet'), findsOneWidget);
      expect(find.byIcon(Icons.notifications_none), findsOneWidget);
    });

    testWidgets('shows notification list', (tester) async {
      final mockApi = MockApiService();
      final mockAuth = MockAuthService();
      when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);

      final notifications = [
        AppNotification(
          id: 1,
          title: 'Fresh picks!',
          body: 'New books for you',
          category: 'recommendations',
          isRead: false,
          createdAt: DateTime.now(),
        ),
        AppNotification(
          id: 2,
          title: 'Friend activity',
          body: 'Alice liked a book',
          category: 'social',
          isRead: true,
          createdAt: DateTime.now().subtract(const Duration(hours: 2)),
        ),
      ];

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(mockApi),
            authServiceProvider.overrideWithValue(mockAuth),
            notificationHistoryProvider.overrideWith(
              () => _StaticHistoryNotifier(NotificationHistoryState(
                notifications: notifications,
                total: 2,
                unreadCount: 1,
              )),
            ),
          ],
          child: const MaterialApp(home: NotificationInboxScreen()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Fresh picks!'), findsOneWidget);
      expect(find.text('Friend activity'), findsOneWidget);
      expect(find.text('Mark all read'), findsOneWidget);
      expect(find.text('Notifications'), findsOneWidget);
    });

    testWidgets('hides mark-all-read button when no unread', (tester) async {
      final mockApi = MockApiService();
      final mockAuth = MockAuthService();
      when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);

      final notifications = [
        AppNotification(
          id: 1,
          title: 'Old notification',
          body: 'Already read',
          category: 'general',
          isRead: true,
          createdAt: DateTime.now().subtract(const Duration(days: 1)),
        ),
      ];

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(mockApi),
            authServiceProvider.overrideWithValue(mockAuth),
            notificationHistoryProvider.overrideWith(
              () => _StaticHistoryNotifier(NotificationHistoryState(
                notifications: notifications,
                total: 1,
                unreadCount: 0,
              )),
            ),
          ],
          child: const MaterialApp(home: NotificationInboxScreen()),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Old notification'), findsOneWidget);
      expect(find.text('Mark all read'), findsNothing);
    });
  });
}

// --- Fake Notifiers for Testing ---

class _StaticPrefsNotifier extends NotificationPreferencesNotifier {
  final NotificationPreferences _prefs;
  _StaticPrefsNotifier(this._prefs);

  @override
  Future<NotificationPreferences> build() async => _prefs;
}

class _StaticHistoryNotifier extends NotificationHistoryNotifier {
  final NotificationHistoryState _state;
  _StaticHistoryNotifier(this._state);

  @override
  Future<NotificationHistoryState> build() async => _state;
}
