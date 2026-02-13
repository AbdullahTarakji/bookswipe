import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';
import 'package:bookswipe/models/user.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/liked_books_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/widgets/shimmer_loading.dart';
import 'package:bookswipe/services/auth_service.dart';
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
  ),
  Book(
    id: 'book2',
    title: '1984',
    authors: ['George Orwell'],
    thumbnailUrl: null,
    averageRating: 4.7,
    categories: ['Dystopian'],
  ),
];

enum _LikedState { data, loading, error }

Widget _buildLikedBooksScreen({
  required MockApiService api,
  required MockAuthService auth,
  List<Book> books = const [],
  _LikedState likedState = _LikedState.data,
  String errorMessage = 'Network error',
}) {
  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      authServiceProvider.overrideWithValue(auth),
      authStateProvider.overrideWith((ref) {
        final notifier = AuthNotifier(
            ref.read(apiServiceProvider), ref.read(authServiceProvider));
        return notifier;
      }),
      likedBooksProvider.overrideWith(
          () => _FakeLikedBooksNotifier(books, likedState, errorMessage)),
    ],
    child: const MaterialApp(home: LikedBooksScreen()),
  );
}

class _FakeLikedBooksNotifier extends LikedBooksNotifier {
  final List<Book> _books;
  final _LikedState _state;
  final String _errorMessage;

  _FakeLikedBooksNotifier(this._books, this._state, this._errorMessage);

  @override
  Future<List<Book>> build() async {
    switch (_state) {
      case _LikedState.data:
        return _books;
      case _LikedState.loading:
        await Completer<List<Book>>().future;
        return []; // unreachable
      case _LikedState.error:
        throw _errorMessage;
    }
  }
}

void main() {
  late MockApiService mockApi;
  late MockAuthService mockAuth;

  setUp(() {
    mockApi = MockApiService();
    mockAuth = MockAuthService();
    when(() => mockAuth.getStoredUser()).thenAnswer((_) async => _testUser);
  });

  group('LikedBooksScreen', () {
    testWidgets('shows app bar with title', (tester) async {
      await tester.pumpWidget(_buildLikedBooksScreen(
        api: mockApi,
        auth: mockAuth,
      ));
      await tester.pumpAndSettle();

      expect(find.text('My Matches'), findsOneWidget);
    });

    testWidgets('shows empty state when no liked books', (tester) async {
      await tester.pumpWidget(_buildLikedBooksScreen(
        api: mockApi,
        auth: mockAuth,
      ));
      await tester.pumpAndSettle();

      expect(find.text('No matches yet'), findsOneWidget);
      expect(find.textContaining('Swipe right on books you love'), findsOneWidget);
      expect(find.byIcon(Icons.favorite_border_rounded), findsOneWidget);
    });

    testWidgets('shows list of liked books', (tester) async {
      await tester.pumpWidget(_buildLikedBooksScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
      ));
      await tester.pumpAndSettle();

      expect(find.text('The Great Gatsby'), findsOneWidget);
      expect(find.text('F. Scott Fitzgerald'), findsOneWidget);
      expect(find.text('1984'), findsOneWidget);
      expect(find.text('George Orwell'), findsOneWidget);
    });

    testWidgets('shows rating badges for rated books', (tester) async {
      await tester.pumpWidget(_buildLikedBooksScreen(
        api: mockApi,
        auth: mockAuth,
        books: _testBooks,
      ));
      await tester.pumpAndSettle();

      expect(find.text('4.2'), findsOneWidget);
      expect(find.text('4.7'), findsOneWidget);
    });

    testWidgets('shows loading indicator', (tester) async {
      await tester.pumpWidget(_buildLikedBooksScreen(
        api: mockApi,
        auth: mockAuth,
        likedState: _LikedState.loading,
      ));
      await tester.pump();

      expect(find.byType(FavoritesShimmer), findsOneWidget);
    });

    testWidgets('shows error view with retry', (tester) async {
      await tester.pumpWidget(_buildLikedBooksScreen(
        api: mockApi,
        auth: mockAuth,
        likedState: _LikedState.error,
        errorMessage: 'Network error',
      ));
      await tester.pumpAndSettle();

      expect(find.textContaining('Network error'), findsOneWidget);
      expect(find.text('Try Again'), findsOneWidget);
    });
  });
}
