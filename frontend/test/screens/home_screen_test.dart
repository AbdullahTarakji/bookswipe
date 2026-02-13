import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';
import 'package:bookswipe/models/user.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/home_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/services/auth_service.dart';
import 'package:bookswipe/widgets/error_view.dart';
import 'package:bookswipe/widgets/shimmer_loading.dart';
import 'package:mocktail/mocktail.dart';

class MockApiService extends Mock implements ApiService {}

class MockAuthService extends Mock implements AuthService {}

const _testUser = User(
  id: '1',
  email: 'test@example.com',
  token: 'test-token',
  refreshToken: 'test-refresh',
);

const _testBooks = [
  Book(
    id: 'book1',
    title: 'The Great Gatsby',
    authors: ['F. Scott Fitzgerald'],
    thumbnailUrl: null,
    averageRating: 4.2,
    categories: ['Fiction'],
    description: 'A classic novel.',
  ),
  Book(
    id: 'book2',
    title: '1984',
    authors: ['George Orwell'],
    thumbnailUrl: null,
    averageRating: 4.7,
    categories: ['Dystopian'],
  ),
  Book(
    id: 'book3',
    title: 'To Kill a Mockingbird',
    authors: ['Harper Lee'],
    thumbnailUrl: null,
    averageRating: 4.4,
    categories: ['Fiction'],
  ),
];

enum _DiscoverState { data, loading, error }

Widget _buildHomeScreen({
  required MockApiService api,
  required MockAuthService auth,
  List<Book> books = const [],
  _DiscoverState discoverState = _DiscoverState.data,
  String errorMessage = 'Failed to load books',
  AsyncValue<User?>? authState,
}) {
  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      authServiceProvider.overrideWithValue(auth),
      if (authState != null)
        authStateProvider.overrideWith((ref) => _FakeAuthNotifier(
            ref.read(apiServiceProvider),
            ref.read(authServiceProvider),
            authState)),
      discoverBooksProvider.overrideWith(
          () => _FakeDiscoverNotifier(books, discoverState, errorMessage)),
      swipeStatusProvider.overrideWith((ref) async {
        return {
          'swipes_today': 3,
          'daily_limit': 10,
          'is_premium': false,
          'swipes_remaining': 7,
        };
      }),
      likedBooksProvider.overrideWith(() => _FakeLikedBooksNotifier()),
    ],
    child: const MaterialApp(home: HomeScreen()),
  );
}

class _FakeAuthNotifier extends AuthNotifier {
  final AsyncValue<User?> _initial;

  _FakeAuthNotifier(super.api, super.auth, this._initial);

  @override
  // ignore: must_call_super
  AsyncValue<User?> get state => _initial;

  @override
  set state(AsyncValue<User?> value) {}
}

class _FakeDiscoverNotifier extends DiscoverBooksNotifier {
  final List<Book> _books;
  final _DiscoverState _state;
  final String _errorMessage;

  _FakeDiscoverNotifier(this._books, this._state, this._errorMessage);

  @override
  Future<List<Book>> build() async {
    switch (_state) {
      case _DiscoverState.data:
        return _books;
      case _DiscoverState.loading:
        await Completer<List<Book>>().future;
        return []; // unreachable
      case _DiscoverState.error:
        throw _errorMessage;
    }
  }
}

class _FakeLikedBooksNotifier extends LikedBooksNotifier {
  @override
  Future<List<Book>> build() async => [];
}

void main() {
  late MockApiService mockApi;
  late MockAuthService mockAuth;

  setUp(() {
    mockApi = MockApiService();
    mockAuth = MockAuthService();
    when(() => mockAuth.getStoredUser()).thenAnswer((_) async => null);
  });

  group('HomeScreen', () {
    testWidgets('shows loading state', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        discoverState: _DiscoverState.loading,
        authState: const AsyncValue.data(null),
      ));
      await tester.pump();

      expect(find.byType(HomeShimmer), findsOneWidget);
    });

    testWidgets('shows error state with retry', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        discoverState: _DiscoverState.error,
        errorMessage: 'Failed to load books',
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.byType(ErrorView), findsOneWidget);
      expect(find.text('Try Again'), findsOneWidget);
    });

    testWidgets('shows empty state when no books', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      expect(find.text('No more books!'), findsOneWidget);
      expect(find.text('Try a different category or check back later.'),
          findsOneWidget);
      expect(find.text('Refresh'), findsOneWidget);
    });

    testWidgets('shows book cards when data available', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // At least the top card's book title should be visible
      expect(find.text('The Great Gatsby'), findsOneWidget);
    });

    testWidgets('shows action buttons when books loaded', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // Action button icons
      expect(find.byIcon(Icons.replay_rounded), findsOneWidget);
      expect(find.byIcon(Icons.close_rounded), findsOneWidget);
      expect(find.byIcon(Icons.star_rounded), findsWidgets);
      expect(find.byIcon(Icons.favorite_rounded), findsOneWidget);
    });

    testWidgets('shows top bar with icons', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // Top bar icons: tune (categories), fire (logo), refresh
      expect(find.byIcon(Icons.tune_rounded), findsOneWidget);
      expect(find.byIcon(Icons.local_fire_department), findsOneWidget);
      expect(find.byIcon(Icons.refresh_rounded), findsOneWidget);
    });

    testWidgets('shows swipe indicator for free users', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
        authState: const AsyncValue.data(_testUser),
      ));
      await tester.pumpAndSettle();

      // Swipe indicator shows remaining count
      expect(find.text('7 left'), findsOneWidget);
      expect(find.byType(LinearProgressIndicator), findsOneWidget);
    });

    testWidgets('no swipe indicator for guest users', (tester) async {
      await tester.pumpWidget(_buildHomeScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
        authState: const AsyncValue.data(null),
      ));
      await tester.pumpAndSettle();

      // No swipe indicator for guests
      expect(find.byType(LinearProgressIndicator), findsNothing);
    });
  });
}
