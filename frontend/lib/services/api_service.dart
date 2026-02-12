import 'package:dio/dio.dart';
import '../models/book.dart';

/// HTTP client service for communicating with the BookSwipe backend API.
class ApiService {
  final Dio _dio;
  String? _refreshToken;
  Future<void> Function(String refreshToken)? onTokenRefreshNeeded;

  ApiService({String? baseUrl, Dio? dio})
      : _dio = dio ?? Dio(BaseOptions(
          baseUrl: baseUrl ?? const String.fromEnvironment(
            'API_BASE_URL',
            defaultValue: 'http://localhost:8000',
          ),
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && _refreshToken != null) {
          try {
            final refreshResponse = await _dio.post(
              '/api/auth/refresh',
              data: {'refresh_token': _refreshToken},
              options: Options(headers: {
                // Don't send the expired token for refresh
                'Authorization': null,
              }),
            );
            final newToken = refreshResponse.data['access_token'] as String;
            final newRefreshToken = refreshResponse.data['refresh_token'] as String;
            setAuthToken(newToken);
            _refreshToken = newRefreshToken;

            if (onTokenRefreshNeeded != null) {
              await onTokenRefreshNeeded!(newRefreshToken);
            }

            // Retry the original request with new token
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer $newToken';
            final response = await _dio.fetch(opts);
            return handler.resolve(response);
          } on DioException {
            return handler.next(error);
          }
        }
        return handler.next(error);
      },
    ));
  }

  /// Set the Bearer token for authenticated requests.
  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  /// Store the refresh token for automatic token renewal.
  void setRefreshToken(String token) {
    _refreshToken = token;
  }

  /// Remove the auth and refresh tokens (used on logout).
  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
    _refreshToken = null;
  }

  /// Discover books by category with pagination.
  Future<List<Book>> discoverBooks({String? category, int page = 1}) async {
    final queryParams = <String, dynamic>{
      'page': page,
    };
    if (category != null) {
      queryParams['category'] = category;
    }
    final response = await _dio.get('/api/books/discover', queryParameters: queryParams);
    final books = response.data['books'] as List<dynamic>;
    return books.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// Get detailed information for a specific book.
  Future<Book> getBookDetails(String bookId) async {
    final response = await _dio.get('/api/books/$bookId');
    return Book.fromJson(response.data as Map<String, dynamic>);
  }

  /// Like a book, sending its metadata to the backend.
  Future<void> likeBook(Book book) async {
    await _dio.post('/api/books/like', data: {
      'google_book_id': book.id,
      'title': book.title,
      'authors': book.authorsText,
      'thumbnail': book.thumbnailUrl ?? '',
    });
  }

  /// Skip a book so it won't appear in future discovery.
  Future<void> skipBook(String bookId) async {
    await _dio.post('/api/books/skip', data: {'google_book_id': bookId});
  }

  /// Fetch the authenticated user's liked books.
  Future<List<Book>> getLikedBooks() async {
    final response = await _dio.get('/api/books/liked');
    final books = response.data['books'] as List<dynamic>;
    return books.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// Remove a book from the user's liked list.
  Future<void> unlikeBook(String bookId) async {
    await _dio.delete('/api/books/liked/$bookId');
  }

  /// Fetch all available book categories.
  Future<List<Map<String, dynamic>>> getCategories() async {
    final response = await _dio.get('/api/categories');
    return (response.data as List<dynamic>)
        .map((c) => c as Map<String, dynamic>)
        .toList();
  }

  /// Fetch the authenticated user's profile.
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _dio.get('/api/auth/me');
    return response.data as Map<String, dynamic>;
  }

  /// Authenticate with email and password, returning token data.
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post('/api/auth/login', data: {
      'email': email,
      'password': password,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Register a new account, returning token data.
  Future<Map<String, dynamic>> register(String email, String password) async {
    final response = await _dio.post('/api/auth/register', data: {
      'email': email,
      'password': password,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Refresh an expired access token using a refresh token.
  Future<Map<String, dynamic>> refreshToken(String refreshToken) async {
    final response = await _dio.post('/api/auth/refresh', data: {
      'refresh_token': refreshToken,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Format a DioException into a user-friendly message
  static String formatError(DioException e) {
    if (e.response != null) {
      final data = e.response!.data;
      if (data is Map<String, dynamic> && data.containsKey('detail')) {
        final detail = data['detail'];
        if (detail is String) return detail;
        if (detail is List && detail.isNotEmpty) {
          return detail.map((d) => d['msg'] ?? d.toString()).join(', ');
        }
        return detail.toString();
      }
      final statusCode = e.response!.statusCode;
      if (statusCode == 401) return 'Please log in to continue';
      if (statusCode == 403) return 'You don\'t have permission to do this';
      if (statusCode == 404) return 'Resource not found';
      if (statusCode == 422) return 'Invalid data provided';
      if (statusCode == 429) return 'Too many requests. Please wait a moment';
      if (statusCode != null && statusCode >= 500) {
        return 'Server error. Please try again later';
      }
    }
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timed out. Check your internet connection';
      case DioExceptionType.connectionError:
        return 'Cannot connect to server. Check your internet connection';
      case DioExceptionType.cancel:
        return 'Request cancelled';
      default:
        return 'Network error. Please try again';
    }
  }
}
