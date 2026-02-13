import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/activity_feed_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/services/auth_service.dart';
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

class MockAuthService extends Mock implements AuthService {}

void main() {
  late MockApiService mockApi;
  late MockAuthService mockAuth;

  setUp(() {
    mockApi = MockApiService();
    mockAuth = MockAuthService();
    when(() => mockApi.getActivityFeed(page: any(named: 'page'), pageSize: any(named: 'pageSize')))
        .thenAnswer((_) async => {
              'events': <dynamic>[],
              'total': 0,
              'page': 1,
              'page_size': 20,
            });
    when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);
  });

  group('ActivityFeedScreen', () {
    testWidgets('renders with app bar title and empty state', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(mockApi),
            authServiceProvider.overrideWithValue(mockAuth),
          ],
          child: const MaterialApp(
            home: ActivityFeedScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Activity Feed'), findsOneWidget);
      expect(find.text('No activity yet'), findsOneWidget);
    });
  });
}
