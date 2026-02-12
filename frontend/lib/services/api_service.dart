import 'dart:math';

import 'package:dio/dio.dart';
import '../models/book.dart';

/// HTTP client for all BookSwipe API interactions.
///
/// Includes automatic token refresh, retry with exponential backoff
/// for transient network errors, and user-friendly error formatting.
class ApiService {
  final Dio _dio;
  String? _refreshToken;

  /// Maximum number of retry attempts for transient errors.
  static const int maxRetries = 3;

  /// Callback invoked when tokens are refreshed via the interceptor.
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
    _dio.interceptors.add(_RetryInterceptor(_dio));
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && _refreshToken != null) {
          try {
            final refreshResponse = await _dio.post(
              '/api/auth/refresh',
              data: {'refresh_token': _refreshToken},
              options: Options(headers: {
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

  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  void setRefreshToken(String token) {
    _refreshToken = token;
  }

  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
    _refreshToken = null;
  }

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

  Future<Book> getBookDetails(String bookId) async {
    final response = await _dio.get('/api/books/$bookId');
    return Book.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> likeBook(Book book) async {
    await _dio.post('/api/books/like', data: {
      'google_book_id': book.id,
      'title': book.title,
      'authors': book.authorsText,
      'thumbnail': book.thumbnailUrl ?? '',
    });
  }

  Future<void> skipBook(String bookId) async {
    await _dio.post('/api/books/skip', data: {'google_book_id': bookId});
  }

  Future<List<Book>> getLikedBooks() async {
    final response = await _dio.get('/api/books/liked');
    final books = response.data['books'] as List<dynamic>;
    return books.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  Future<void> unlikeBook(String bookId) async {
    await _dio.delete('/api/books/liked/$bookId');
  }

  Future<List<Map<String, dynamic>>> getCategories() async {
    final response = await _dio.get('/api/categories');
    return (response.data as List<dynamic>)
        .map((c) => c as Map<String, dynamic>)
        .toList();
  }

  Future<Map<String, dynamic>> getProfile() async {
    final response = await _dio.get('/api/auth/me');
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post('/api/auth/login', data: {
      'email': email,
      'password': password,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> register(String email, String password) async {
    final response = await _dio.post('/api/auth/register', data: {
      'email': email,
      'password': password,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> refreshToken(String refreshToken) async {
    final response = await _dio.post('/api/auth/refresh', data: {
      'refresh_token': refreshToken,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Format a DioException into a user-friendly message.
  ///
  /// Handles the structured error format `{"error": {"message": ...}}` from
  /// the backend, as well as the legacy `{"detail": ...}` format and raw
  /// HTTP status codes.
  static String formatError(DioException e) {
    if (e.response != null) {
      final data = e.response!.data;
      if (data is Map<String, dynamic>) {
        // New structured error format
        if (data.containsKey('error')) {
          final error = data['error'];
          if (error is Map<String, dynamic> && error.containsKey('message')) {
            return error['message'] as String;
          }
        }
        // Legacy detail format
        if (data.containsKey('detail')) {
          final detail = data['detail'];
          if (detail is String) return detail;
          if (detail is List && detail.isNotEmpty) {
            return detail.map((d) => d['msg'] ?? d.toString()).join(', ');
          }
          return detail.toString();
        }
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

/// Dio interceptor that retries failed requests with exponential backoff.
///
/// Only retries on transient network errors (timeouts, connection errors).
/// Auth errors and client errors (4xx) are not retried.
class _RetryInterceptor extends Interceptor {
  final Dio _dio;

  _RetryInterceptor(this._dio);

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (!_shouldRetry(err)) {
      return handler.next(err);
    }

    final retryCount = err.requestOptions.extra['retryCount'] as int? ?? 0;
    if (retryCount >= ApiService.maxRetries) {
      return handler.next(err);
    }

    final delay = Duration(
      milliseconds: (pow(2, retryCount) * 500).toInt(),
    );
    await Future.delayed(delay);

    try {
      err.requestOptions.extra['retryCount'] = retryCount + 1;
      final response = await _dio.fetch(err.requestOptions);
      return handler.resolve(response);
    } on DioException catch (e) {
      return handler.next(e);
    }
  }

  bool _shouldRetry(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError;
  }
}
