import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:bookswipe/models/book.dart';
import 'package:bookswipe/services/api_service.dart';

import '../helpers/mock_dio_adapter.dart';

void main() {
  late ApiService apiService;
  late MockDioAdapter mockAdapter;
  late Dio dio;

  setUp(() {
    dio = Dio(BaseOptions(
      baseUrl: 'http://localhost:8000',
      headers: {'Content-Type': 'application/json'},
    ));
    mockAdapter = MockDioAdapter();
    dio.httpClientAdapter = mockAdapter;
    apiService = ApiService(dio: dio);
  });

  group('discoverBooks', () {
    test('parses discover response with books key', () async {
      mockAdapter.setResponse(
        200,
        {
          'books': [
            {
              'google_book_id': 'book1',
              'title': 'First Book',
              'authors': ['Author A'],
              'thumbnail': 'https://example.com/thumb1.jpg',
              'categories': ['Fiction'],
              'average_rating': 4.0,
              'ratings_count': 100,
            },
            {
              'google_book_id': 'book2',
              'title': 'Second Book',
              'authors': ['Author B', 'Author C'],
              'thumbnail': 'https://example.com/thumb2.jpg',
              'categories': ['Science'],
              'average_rating': null,
              'ratings_count': null,
            },
          ],
          'total': 2,
          'page': 1,
          'page_size': 20,
        },
      );

      final books = await apiService.discoverBooks();

      expect(books, hasLength(2));
      expect(books[0].id, 'book1');
      expect(books[0].title, 'First Book');
      expect(books[0].authors, ['Author A']);
      expect(books[0].thumbnailUrl, 'https://example.com/thumb1.jpg');
      expect(books[0].averageRating, 4.0);
      expect(books[1].id, 'book2');
      expect(books[1].authors, ['Author B', 'Author C']);
      expect(books[1].averageRating, isNull);
    });

    test('passes category query parameter when provided', () async {
      mockAdapter.setResponse(200, {
        'books': [],
        'total': 0,
        'page': 1,
        'page_size': 20,
      });

      await apiService.discoverBooks(category: 'fiction', page: 2);

      final uri = mockAdapter.lastRequestUri;
      expect(uri?.queryParameters['category'], 'fiction');
      expect(uri?.queryParameters['page'], '2');
    });

    test('omits category when null', () async {
      mockAdapter.setResponse(200, {
        'books': [],
        'total': 0,
        'page': 1,
        'page_size': 20,
      });

      await apiService.discoverBooks();

      final uri = mockAdapter.lastRequestUri;
      expect(uri?.queryParameters.containsKey('category'), isFalse);
      expect(uri?.queryParameters['page'], '1');
    });
  });

  group('likeBook', () {
    test('sends book data with title, authors, and thumbnail', () async {
      mockAdapter.setResponse(200, {'status': 'ok'});

      const book = Book(
        id: 'book1',
        title: 'Test Book',
        authors: ['Author A', 'Author B'],
        thumbnailUrl: 'https://example.com/thumb.jpg',
      );

      await apiService.likeBook(book);

      final data = mockAdapter.lastRequestData;
      expect(data['google_book_id'], 'book1');
      expect(data['title'], 'Test Book');
      expect(data['authors'], 'Author A, Author B');
      expect(data['thumbnail'], 'https://example.com/thumb.jpg');
    });
  });

  group('getLikedBooks', () {
    test('parses liked books with authors as string', () async {
      mockAdapter.setResponse(200, {
        'books': [
          {
            'id': 1,
            'google_book_id': 'liked1',
            'title': 'Liked Book',
            'authors': 'Jane Doe, John Smith',
            'thumbnail': 'https://example.com/liked.jpg',
            'liked_at': '2024-01-15T10:30:00',
          },
        ],
        'total': 1,
        'page': 1,
        'page_size': 20,
      });

      final books = await apiService.getLikedBooks();

      expect(books, hasLength(1));
      expect(books[0].id, 'liked1');
      expect(books[0].title, 'Liked Book');
      expect(books[0].authors, ['Jane Doe', 'John Smith']);
      expect(books[0].authorsText, 'Jane Doe, John Smith');
    });
  });

  group('getCategories', () {
    test('parses categories list', () async {
      mockAdapter.setResponse(200, [
        {'id': 1, 'name': 'Fiction', 'google_category_key': 'fiction'},
        {'id': 2, 'name': 'Science', 'google_category_key': 'science'},
        {'id': 3, 'name': 'Romance', 'google_category_key': 'romance'},
      ]);

      final categories = await apiService.getCategories();

      expect(categories, hasLength(3));
      expect(categories[0]['name'], 'Fiction');
      expect(categories[0]['google_category_key'], 'fiction');
      expect(categories[1]['name'], 'Science');
      expect(categories[2]['name'], 'Romance');
    });
  });

  group('getBookDetails', () {
    test('parses single book detail', () async {
      mockAdapter.setResponse(200, {
        'google_book_id': 'detail1',
        'title': 'Detailed Book',
        'authors': ['Author X'],
        'thumbnail': 'https://example.com/detail.jpg',
        'description': 'A full description of the book.',
        'page_count': 400,
        'average_rating': 4.5,
        'ratings_count': 250,
        'categories': ['Thriller'],
      });

      final book = await apiService.getBookDetails('detail1');

      expect(book.id, 'detail1');
      expect(book.title, 'Detailed Book');
      expect(book.description, 'A full description of the book.');
      expect(book.pageCount, 400);
      expect(book.averageRating, 4.5);
    });
  });

  group('auth', () {
    test('login returns token response', () async {
      mockAdapter.setResponse(200, {
        'access_token': 'test-access-token',
        'refresh_token': 'test-refresh-token',
        'token_type': 'bearer',
      });

      final result = await apiService.login('test@example.com', 'password123');

      expect(result['access_token'], 'test-access-token');
      expect(result['refresh_token'], 'test-refresh-token');
      expect(result['token_type'], 'bearer');
    });

    test('register returns token response', () async {
      mockAdapter.setResponse(200, {
        'access_token': 'new-access-token',
        'refresh_token': 'new-refresh-token',
        'token_type': 'bearer',
      });

      final result = await apiService.register('new@example.com', 'password123');

      expect(result['access_token'], 'new-access-token');
      expect(result['refresh_token'], 'new-refresh-token');
    });

    test('getProfile returns user info', () async {
      mockAdapter.setResponse(200, {
        'id': 42,
        'email': 'user@example.com',
        'created_at': '2024-01-01T00:00:00',
      });

      final profile = await apiService.getProfile();

      expect(profile['id'], 42);
      expect(profile['email'], 'user@example.com');
    });
  });

  group('error handling', () {
    test('formatError extracts detail from response', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/test'),
        response: Response(
          requestOptions: RequestOptions(path: '/test'),
          statusCode: 400,
          data: {'detail': 'Email already registered'},
        ),
      );

      expect(ApiService.formatError(error), 'Email already registered');
    });

    test('formatError handles 401 without detail', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/test'),
        response: Response(
          requestOptions: RequestOptions(path: '/test'),
          statusCode: 401,
          data: {},
        ),
      );

      expect(ApiService.formatError(error), 'Please log in to continue');
    });

    test('formatError handles connection timeout', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/test'),
        type: DioExceptionType.connectionTimeout,
      );

      expect(ApiService.formatError(error), contains('timed out'));
    });

    test('formatError handles connection error', () {
      final error = DioException(
        requestOptions: RequestOptions(path: '/test'),
        type: DioExceptionType.connectionError,
      );

      expect(ApiService.formatError(error), contains('Cannot connect'));
    });
  });

  group('payments', () {
    test('getSubscription returns subscription data', () async {
      mockAdapter.setResponse(200, {
        'subscription_status': 'active',
        'subscription_plan': 'premium',
        'is_premium': true,
        'subscription_end_date': '2025-12-31T00:00:00',
      });

      final result = await apiService.getSubscription();

      expect(result['subscription_status'], 'active');
      expect(result['subscription_plan'], 'premium');
      expect(result['is_premium'], isTrue);
    });

    test('createCheckoutSession returns checkout URL', () async {
      mockAdapter.setResponse(200, {
        'checkout_url': 'https://checkout.stripe.com/session123',
      });

      final url = await apiService.createCheckoutSession();

      expect(url, 'https://checkout.stripe.com/session123');
    });

    test('cancelSubscription completes without error', () async {
      mockAdapter.setResponse(200, {'message': 'Subscription cancelled'});

      await apiService.cancelSubscription();
      // No exception = success
    });

    test('createBillingPortalSession returns portal URL', () async {
      mockAdapter.setResponse(200, {
        'checkout_url': 'https://billing.stripe.com/portal123',
      });

      final url = await apiService.createBillingPortalSession();

      expect(url, 'https://billing.stripe.com/portal123');
    });

    test('getSwipeStatus returns swipe data', () async {
      mockAdapter.setResponse(200, {
        'swipes_today': 5,
        'daily_limit': 10,
        'is_premium': false,
        'swipes_remaining': 5,
      });

      final result = await apiService.getSwipeStatus();

      expect(result['swipes_today'], 5);
      expect(result['daily_limit'], 10);
      expect(result['is_premium'], isFalse);
      expect(result['swipes_remaining'], 5);
    });
  });

  group('token management', () {
    test('setAuthToken adds bearer header', () {
      apiService.setAuthToken('my-token');
      expect(dio.options.headers['Authorization'], 'Bearer my-token');
    });

    test('clearAuthToken removes header and refresh token', () {
      apiService.setAuthToken('my-token');
      apiService.setRefreshToken('my-refresh');
      apiService.clearAuthToken();
      expect(dio.options.headers.containsKey('Authorization'), isFalse);
    });
  });
}
