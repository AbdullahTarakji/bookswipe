import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/social_profile_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

void main() {
  late MockApiService mockApi;

  setUp(() {
    mockApi = MockApiService();
    when(() => mockApi.getSocialProfile()).thenAnswer((_) async => {
          'user_id': 1,
          'username': 'testuser',
          'bio': 'Hello world',
          'avatar_url': null,
          'is_public': true,
          'reading_goal': 24,
          'followers_count': 5,
          'following_count': 3,
          'books_liked_count': 10,
          'is_following': false,
        });
  });

  group('SocialProfileScreen', () {
    testWidgets('renders profile screen with username after loading', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [apiServiceProvider.overrideWithValue(mockApi)],
          child: const MaterialApp(
            home: SocialProfileScreen(),
          ),
        ),
      );

      // Shows loading initially
      expect(find.text('Profile'), findsOneWidget);

      // Wait for async load
      await tester.pumpAndSettle();

      // Shows profile data
      expect(find.text('testuser'), findsNWidgets(2)); // AppBar + body
      expect(find.text('Hello world'), findsOneWidget);
      expect(find.text('5'), findsOneWidget); // followers
      expect(find.text('3'), findsOneWidget); // following
    });
  });
}
