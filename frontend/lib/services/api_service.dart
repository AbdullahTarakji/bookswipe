import 'package:dio/dio.dart';
import '../models/book.dart';

class ApiService {
  final Dio _dio;

  ApiService({String? baseUrl})
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl ?? const String.fromEnvironment(
            'API_BASE_URL',
            defaultValue: 'http://localhost:8000',
          ),
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        ));

  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
  }

  Future<List<Book>> discoverBooks({String? category, int page = 1}) async {
    final response = await _dio.get('/api/books/discover', queryParameters: {
      'category': ?category,
      'page': page,
    });
    final items = response.data['items'] as List<dynamic>? ??
        response.data['books'] as List<dynamic>? ??
        response.data as List<dynamic>;
    return items.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  Future<Book> getBookDetails(String bookId) async {
    final response = await _dio.get('/api/books/$bookId');
    return Book.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> likeBook(String bookId) async {
    await _dio.post('/api/books/like', data: {'google_book_id': bookId});
  }

  Future<void> skipBook(String bookId) async {
    await _dio.post('/api/books/skip', data: {'google_book_id': bookId});
  }

  Future<List<Book>> getLikedBooks() async {
    final response = await _dio.get('/api/books/liked');
    final items = response.data['items'] as List<dynamic>? ??
        response.data['books'] as List<dynamic>? ??
        response.data as List<dynamic>;
    return items.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  Future<void> unlikeBook(String bookId) async {
    await _dio.delete('/api/books/liked/$bookId');
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
}
