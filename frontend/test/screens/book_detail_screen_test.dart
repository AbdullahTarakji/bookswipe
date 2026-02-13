import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';
import 'package:bookswipe/models/user.dart';
import 'package:bookswipe/providers/providers.dart';
import 'package:bookswipe/screens/book_detail_screen.dart';
import 'package:bookswipe/services/api_service.dart';
import 'package:bookswipe/services/auth_service.dart';
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

const _testBook = Book(
  id: 'detail1',
  title: 'Test Book Title',
  authors: ['Author One', 'Author Two'],
  description: 'A fascinating book about testing.',
  thumbnailUrl: null,
  pageCount: 350,
  averageRating: 4.5,
  ratingsCount: 200,
  categories: ['Fiction', 'Adventure'],
  publishedDate: '2023-06-15',
  publisher: 'Test Publisher Co',
);

/// Build parameter to control how the book detail provider behaves.
enum _BookDetailState { data, loading, error }

Widget _buildBookDetailScreen({
  required MockApiService api,
  required MockAuthService auth,
  required String bookId,
  Book book = _testBook,
  _BookDetailState detailState = _BookDetailState.data,
  String errorMessage = 'Failed to load',
  List<Book> likedBooks = const [],
}) {
  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      authServiceProvider.overrideWithValue(auth),
      authStateProvider.overrideWith((ref) => AuthNotifier(
          ref.read(apiServiceProvider), ref.read(authServiceProvider))),
      bookDetailProvider(bookId).overrideWith((ref) async {
        switch (detailState) {
          case _BookDetailState.data:
            return book;
          case _BookDetailState.loading:
            // Never completes => stays in loading
            await Completer<Book>().future;
            return book; // unreachable
          case _BookDetailState.error:
            throw errorMessage;
        }
      }),
      likedBooksProvider.overrideWith(() => _FakeLikedBooksNotifier(likedBooks)),
    ],
    child: MaterialApp(home: BookDetailScreen(bookId: bookId)),
  );
}

class _FakeLikedBooksNotifier extends LikedBooksNotifier {
  final List<Book> _books;

  _FakeLikedBooksNotifier(this._books);

  @override
  Future<List<Book>> build() async => _books;
}

void main() {
  late MockApiService mockApi;
  late MockAuthService mockAuth;

  setUp(() {
    mockApi = MockApiService();
    mockAuth = MockAuthService();
    when(() => mockAuth.getStoredUser()).thenAnswer((_) async => _testUser);
  });

  group('BookDetailScreen', () {
    testWidgets('shows book title and authors', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
      ));
      await tester.pumpAndSettle();

      expect(find.text('Test Book Title'), findsOneWidget);
      expect(find.text('Author One, Author Two'), findsOneWidget);
    });

    testWidgets('shows book metadata (rating, pages)', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
      ));
      await tester.pumpAndSettle();

      expect(find.text('4.5'), findsOneWidget);
      expect(find.text('350 pages'), findsOneWidget);
      expect(find.text('(200 reviews)'), findsOneWidget);
    });

    testWidgets('shows description section', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
      ));
      await tester.pumpAndSettle();

      expect(find.text('Description'), findsOneWidget);
      expect(find.text('A fascinating book about testing.'), findsOneWidget);
    });

    testWidgets('shows category chips', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
      ));
      await tester.pumpAndSettle();

      expect(find.text('Fiction'), findsOneWidget);
      expect(find.text('Adventure'), findsOneWidget);
    });

    testWidgets('shows publication info', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
      ));
      await tester.pumpAndSettle();

      expect(find.text('Publication Info'), findsOneWidget);
      expect(find.textContaining('Test Publisher Co'), findsOneWidget);
      expect(find.textContaining('2023-06-15'), findsOneWidget);
    });

    testWidgets('shows like button when not liked', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
        likedBooks: const [],
      ));
      await tester.pumpAndSettle();

      expect(find.text('Like this Book'), findsOneWidget);
      expect(find.byIcon(Icons.favorite_border), findsOneWidget);
    });

    testWidgets('shows unlike button when already liked', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
        likedBooks: const [_testBook],
      ));
      await tester.pumpAndSettle();

      expect(find.text('Remove from Liked'), findsOneWidget);
      expect(find.byIcon(Icons.favorite), findsOneWidget);
    });

    testWidgets('shows loading state', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
        detailState: _BookDetailState.loading,
      ));
      await tester.pump();

      expect(find.byType(BookDetailShimmer), findsOneWidget);
    });

    testWidgets('shows error state with retry', (tester) async {
      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'detail1',
        detailState: _BookDetailState.error,
        errorMessage: 'Failed to load',
      ));
      await tester.pumpAndSettle();

      expect(find.textContaining('Failed to load'), findsOneWidget);
      expect(find.text('Try Again'), findsOneWidget);
    });

    testWidgets('hides description when null', (tester) async {
      const bookNoDesc = Book(
        id: 'nodesc',
        title: 'No Description',
        authors: ['Author'],
      );

      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'nodesc',
        book: bookNoDesc,
      ));
      await tester.pumpAndSettle();

      expect(find.text('Description'), findsNothing);
    });

    testWidgets('hides publication info when not available', (tester) async {
      const bookNoPub = Book(
        id: 'nopub',
        title: 'No Publisher',
        authors: ['Author'],
      );

      await tester.pumpWidget(_buildBookDetailScreen(
        api: mockApi,
        auth: mockAuth,
        bookId: 'nopub',
        book: bookNoPub,
      ));
      await tester.pumpAndSettle();

      expect(find.text('Publication Info'), findsNothing);
    });
  });
}
