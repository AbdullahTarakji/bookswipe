import 'dart:async';
import 'dart:math';
import 'package:dio/dio.dart';
import '../models/book.dart';

/// HTTP client for the BookSwipe API with automatic token refresh and retry logic.
class ApiService {
  final Dio _dio;
  String? _refreshToken;

  /// Callback invoked when the auth token is refreshed so the caller can persist it.
  Future<void> Function(String accessToken, String refreshToken)? onTokenRefreshNeeded;

  /// Maximum number of automatic retries for network errors.
  static const int maxRetries = 3;

  /// Base delay for exponential backoff (doubles with each retry).
  static const Duration baseRetryDelay = Duration(milliseconds: 500);

  /// Derive the API base URL from the current page origin.
  static String get _defaultBaseUrl {
    const env = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (env.isNotEmpty) return env;
    // Use window origin for same-origin requests
    try {
      final uri = Uri.base;
      if (uri.host.isNotEmpty) {
        return uri.origin;
      }
    } catch (_) {}
    return 'http://localhost:8080';
  }

  /// Creates an [ApiService] with an optional [baseUrl] or pre-configured [dio] instance.
  ApiService({String? baseUrl, Dio? dio})
      : _dio = dio ?? Dio(BaseOptions(
          baseUrl: baseUrl ?? _defaultBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && _refreshToken != null) {
          try {
            // Use a fresh Dio instance so the expired Authorization header is not sent
            final refreshDio = Dio(BaseOptions(
              baseUrl: _dio.options.baseUrl,
              connectTimeout: _dio.options.connectTimeout,
              receiveTimeout: _dio.options.receiveTimeout,
              headers: {'Content-Type': 'application/json'},
            ));
            final refreshResponse = await refreshDio.post(
              '/api/auth/refresh',
              data: {'refresh_token': _refreshToken},
            );
            final newToken = refreshResponse.data['access_token'] as String;
            final newRefreshToken = refreshResponse.data['refresh_token'] as String;
            setAuthToken(newToken);
            _refreshToken = newRefreshToken;

            if (onTokenRefreshNeeded != null) {
              await onTokenRefreshNeeded!(newToken, newRefreshToken);
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

  /// Set the Bearer token used for authenticated requests.
  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  /// Store the refresh token for automatic token renewal.
  void setRefreshToken(String token) {
    _refreshToken = token;
  }

  /// Remove all authentication tokens.
  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
    _refreshToken = null;
  }

  /// Execute a request with exponential backoff retry for transient network errors.
  ///
  /// Retries up to [maxRetries] times for connection timeouts, send timeouts,
  /// and connection errors. Non-retryable errors are rethrown immediately.
  Future<Response<T>> _requestWithRetry<T>(Future<Response<T>> Function() request) async {
    var attempt = 0;
    while (true) {
      try {
        return await request();
      } on DioException catch (e) {
        attempt++;
        if (!_isRetryable(e) || attempt >= maxRetries) {
          rethrow;
        }
        final delay = baseRetryDelay * pow(2, attempt - 1);
        await Future<void>.delayed(delay);
      }
    }
  }

  /// Returns true if the error type is transient and worth retrying.
  bool _isRetryable(DioException e) {
    return e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionError;
  }

  /// Discover books by category with pagination.
  Future<List<Book>> discoverBooks({String? category, int page = 1}) async {
    final queryParams = <String, dynamic>{
      'page': page,
    };
    if (category != null) {
      queryParams['category'] = category;
    }
    final response = await _requestWithRetry(
      () => _dio.get('/api/books/discover', queryParameters: queryParams),
    );
    final books = response.data['books'] as List<dynamic>;
    return books.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// Fetch detailed information for a single book.
  Future<Book> getBookDetails(String bookId) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/books/$bookId'),
    );
    return Book.fromJson(response.data as Map<String, dynamic>);
  }

  /// Like a book (add to the user's liked list).
  Future<void> likeBook(Book book) async {
    await _requestWithRetry(
      () => _dio.post('/api/books/like', data: {
        'google_book_id': book.id,
        'title': book.title,
        'authors': book.authorsText,
        'thumbnail': book.thumbnailUrl ?? '',
      }),
    );
  }

  /// Save selected genre preferences from onboarding.
  Future<void> updateGenrePreferences(List<String> genres) async {
    await _requestWithRetry(
      () => _dio.put('/api/books/preferences', data: {'genres': genres}),
    );
  }

  /// Skip a book (mark as not interested).
  Future<void> skipBook(String bookId) async {
    await _requestWithRetry(
      () => _dio.post('/api/books/skip', data: {'google_book_id': bookId}),
    );
  }

  /// Fetch the authenticated user's liked books.
  Future<List<Book>> getLikedBooks() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/books/liked'),
    );
    final books = response.data['books'] as List<dynamic>;
    return books.map((json) => Book.fromJson(json as Map<String, dynamic>)).toList();
  }

  /// Remove a book from the user's liked list.
  Future<void> unlikeBook(String bookId) async {
    await _requestWithRetry(
      () => _dio.delete('/api/books/liked/$bookId'),
    );
  }

  /// Fetch available book categories from the API.
  Future<List<Map<String, dynamic>>> getCategories() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/categories'),
    );
    return (response.data as List<dynamic>)
        .map((c) => c as Map<String, dynamic>)
        .toList();
  }

  /// Fetch the authenticated user's profile.
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/auth/me'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Authenticate with email and password.
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post('/api/auth/login', data: {
      'email': email,
      'password': password,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Register a new account with email and password.
  Future<Map<String, dynamic>> register(String email, String password) async {
    final response = await _dio.post('/api/auth/register', data: {
      'email': email,
      'password': password,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Authenticate with a Google OAuth ID token.
  Future<Map<String, dynamic>> googleSignIn(String idToken) async {
    final response = await _dio.post('/api/auth/google', data: {
      'id_token': idToken,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Authenticate with Apple OAuth credentials.
  Future<Map<String, dynamic>> appleSignIn({
    required String authorizationCode,
    required String identityToken,
  }) async {
    final response = await _dio.post('/api/auth/apple', data: {
      'authorization_code': authorizationCode,
      'identity_token': identityToken,
    });
    return response.data as Map<String, dynamic>;
  }

  /// Exchange a refresh token for new access and refresh tokens.
  Future<Map<String, dynamic>> refreshToken(String refreshToken) async {
    final response = await _dio.post('/api/auth/refresh', data: {
      'refresh_token': refreshToken,
    });
    return response.data as Map<String, dynamic>;
  }

  // --- Payments / Subscriptions ---

  /// Get the current user's subscription status.
  Future<Map<String, dynamic>> getSubscription() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/payments/subscription'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Create a Stripe checkout session and return the checkout URL.
  Future<String> createCheckoutSession() async {
    final response = await _requestWithRetry(
      () => _dio.post('/api/payments/create-checkout'),
    );
    return (response.data as Map<String, dynamic>)['checkout_url'] as String;
  }

  /// Cancel the current subscription.
  Future<void> cancelSubscription() async {
    await _requestWithRetry(
      () => _dio.post('/api/payments/cancel'),
    );
  }

  /// Create a billing portal session and return the URL.
  Future<String> createBillingPortalSession() async {
    final response = await _requestWithRetry(
      () => _dio.post('/api/payments/portal'),
    );
    return (response.data as Map<String, dynamic>)['checkout_url'] as String;
  }

  /// Get the current user's swipe limit status.
  Future<Map<String, dynamic>> getSwipeStatus() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/payments/swipe-status'),
    );
    return response.data as Map<String, dynamic>;
  }

  // --- Admin endpoints ---

  /// Fetch paginated list of users for admin panel.
  Future<Map<String, dynamic>> getAdminUsers({
    int page = 1,
    int pageSize = 20,
    String? search,
    String? role,
    bool? isBanned,
  }) async {
    final queryParams = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
    };
    if (search != null && search.isNotEmpty) queryParams['search'] = search;
    if (role != null) queryParams['role'] = role;
    if (isBanned != null) queryParams['is_banned'] = isBanned;

    final response = await _requestWithRetry(
      () => _dio.get('/api/admin/users', queryParameters: queryParams),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Fetch a single user's details for admin panel.
  Future<Map<String, dynamic>> getAdminUser(int userId) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/admin/users/$userId'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Update a user's role.
  Future<Map<String, dynamic>> updateUserRole(int userId, String role) async {
    final response = await _dio.put(
      '/api/admin/users/$userId/role',
      data: {'role': role},
    );
    return response.data as Map<String, dynamic>;
  }

  /// Ban or unban a user (toggle).
  Future<Map<String, dynamic>> toggleBanUser(int userId, {String? reason}) async {
    final response = await _dio.put(
      '/api/admin/users/$userId/ban',
      data: {'reason': reason},
    );
    return response.data as Map<String, dynamic>;
  }

  /// Hard-delete a user.
  Future<void> deleteUser(int userId) async {
    await _dio.delete('/api/admin/users/$userId');
  }

  /// Fetch admin analytics.
  Future<Map<String, dynamic>> getAnalytics() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/admin/analytics'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Fetch detailed analytics for the analytics dashboard.
  Future<Map<String, dynamic>> getDetailedAnalytics() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/admin/analytics/detailed'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Fetch system info.
  Future<Map<String, dynamic>> getSystemInfo() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/admin/system'),
    );
    return response.data as Map<String, dynamic>;
  }

  // --- Notifications ---

  /// Register an FCM device token for push notifications.
  Future<void> registerDeviceToken(String token, {String platform = 'android'}) async {
    await _requestWithRetry(
      () => _dio.post('/api/notifications/register-device', data: {
        'token': token,
        'platform': platform,
      }),
    );
  }

  /// Unregister an FCM device token.
  Future<void> unregisterDeviceToken(String token) async {
    await _requestWithRetry(
      () => _dio.post('/api/notifications/unregister-device', data: {
        'token': token,
      }),
    );
  }

  /// Fetch notification preferences.
  Future<Map<String, dynamic>> getNotificationPreferences() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/notifications/preferences'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Update notification preferences.
  Future<Map<String, dynamic>> updateNotificationPreferences({
    bool? recommendations,
    bool? social,
    bool? marketing,
  }) async {
    final data = <String, dynamic>{};
    if (recommendations != null) data['recommendations'] = recommendations;
    if (social != null) data['social'] = social;
    if (marketing != null) data['marketing'] = marketing;

    final response = await _requestWithRetry(
      () => _dio.put('/api/notifications/preferences', data: data),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Fetch notification history with pagination.
  Future<Map<String, dynamic>> getNotificationHistory({int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/notifications/history', queryParameters: {
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Mark a notification as read.
  Future<void> markNotificationRead(int notificationId) async {
    await _requestWithRetry(
      () => _dio.post('/api/notifications/history/$notificationId/read'),
    );
  }

  /// Mark all notifications as read.
  Future<void> markAllNotificationsRead() async {
    await _requestWithRetry(
      () => _dio.post('/api/notifications/history/read-all'),
    );
  }

  // --- Social / Profile ---

  /// Fetch the authenticated user's social profile.
  Future<Map<String, dynamic>> getSocialProfile() async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/profile'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Update the authenticated user's social profile.
  Future<Map<String, dynamic>> updateSocialProfile({
    String? bio,
    String? avatarUrl,
    bool? isPublic,
    int? readingGoal,
  }) async {
    final data = <String, dynamic>{};
    if (bio != null) data['bio'] = bio;
    if (avatarUrl != null) data['avatar_url'] = avatarUrl;
    if (isPublic != null) data['is_public'] = isPublic;
    if (readingGoal != null) data['reading_goal'] = readingGoal;

    final response = await _requestWithRetry(
      () => _dio.put('/api/profile', data: data),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Fetch a public user's profile.
  Future<Map<String, dynamic>> getUserProfile(int userId) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/profile/$userId'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Follow a user.
  Future<void> followUser(int userId) async {
    await _requestWithRetry(
      () => _dio.post('/api/social/follow/$userId'),
    );
  }

  /// Unfollow a user.
  Future<void> unfollowUser(int userId) async {
    await _requestWithRetry(
      () => _dio.delete('/api/social/follow/$userId'),
    );
  }

  /// Get followers list.
  Future<Map<String, dynamic>> getFollowers({int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/social/followers', queryParameters: {
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Get following list.
  Future<Map<String, dynamic>> getFollowing({int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/social/following', queryParameters: {
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Get activity feed.
  Future<Map<String, dynamic>> getActivityFeed({int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/social/feed', queryParameters: {
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Search for users.
  Future<Map<String, dynamic>> searchUsers(String query, {int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/social/search', queryParameters: {
        'q': query,
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  // --- Search ---

  /// Unified search across books, users, and lists.
  Future<Map<String, dynamic>> unifiedSearch(
    String query, {
    String searchType = 'all',
    String? category,
    String? author,
    double? minRating,
    int? yearFrom,
    int? yearTo,
    int page = 1,
    int pageSize = 10,
  }) async {
    final params = <String, dynamic>{
      'q': query,
      'search_type': searchType,
      'page': page,
      'page_size': pageSize,
    };
    if (category != null) params['category'] = category;
    if (author != null) params['author'] = author;
    if (minRating != null) params['min_rating'] = minRating;
    if (yearFrom != null) params['year_from'] = yearFrom;
    if (yearTo != null) params['year_to'] = yearTo;

    final response = await _requestWithRetry(
      () => _dio.get('/api/search', queryParameters: params),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Get autocomplete suggestions.
  Future<List<String>> getAutocompleteSuggestions(String query, {int limit = 5}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/search/autocomplete', queryParameters: {
        'q': query,
        'limit': limit,
      }),
    );
    final data = response.data as Map<String, dynamic>;
    return (data['suggestions'] as List<dynamic>).cast<String>();
  }

  /// Get search history.
  Future<Map<String, dynamic>> getSearchHistory({int limit = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/search/history', queryParameters: {'limit': limit}),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Clear all search history.
  Future<void> clearSearchHistory() async {
    await _requestWithRetry(() => _dio.delete('/api/search/history'));
  }

  /// Delete a single search history item.
  Future<void> deleteSearchHistoryItem(int itemId) async {
    await _requestWithRetry(() => _dio.delete('/api/search/history/$itemId'));
  }

  /// Get trending searches.
  Future<Map<String, dynamic>> getTrendingSearches({int limit = 10}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/search/trending', queryParameters: {'limit': limit}),
    );
    return response.data as Map<String, dynamic>;
  }

  // --- Book Lists ---

  /// Create a new book list.
  Future<Map<String, dynamic>> createBookList({
    required String name,
    String description = '',
    bool isPublic = true,
  }) async {
    final response = await _requestWithRetry(
      () => _dio.post('/api/book-lists', data: {
        'name': name,
        'description': description,
        'is_public': isPublic,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Get the user's book lists.
  Future<Map<String, dynamic>> getBookLists({int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/book-lists', queryParameters: {
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Get a book list with items.
  Future<Map<String, dynamic>> getBookList(int listId) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/book-lists/$listId'),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Update a book list.
  Future<Map<String, dynamic>> updateBookList(int listId, {
    String? name,
    String? description,
    bool? isPublic,
  }) async {
    final data = <String, dynamic>{};
    if (name != null) data['name'] = name;
    if (description != null) data['description'] = description;
    if (isPublic != null) data['is_public'] = isPublic;

    final response = await _requestWithRetry(
      () => _dio.put('/api/book-lists/$listId', data: data),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Delete a book list.
  Future<void> deleteBookList(int listId) async {
    await _requestWithRetry(
      () => _dio.delete('/api/book-lists/$listId'),
    );
  }

  /// Add a book to a list.
  Future<Map<String, dynamic>> addBookToList(int listId, String bookId, {String note = ''}) async {
    final response = await _requestWithRetry(
      () => _dio.post('/api/book-lists/$listId/books', data: {
        'book_id': bookId,
        'note': note,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Remove a book from a list.
  Future<void> removeBookFromList(int listId, String bookId) async {
    await _requestWithRetry(
      () => _dio.delete('/api/book-lists/$listId/books/$bookId'),
    );
  }

  /// Reorder books within a list.
  Future<List<dynamic>> reorderBookList(int listId, List<String> bookIds) async {
    final response = await _requestWithRetry(
      () => _dio.put('/api/book-lists/$listId/reorder', data: {
        'book_ids': bookIds,
      }),
    );
    return response.data as List<dynamic>;
  }

  /// Browse public book lists from other users.
  Future<Map<String, dynamic>> browsePublicLists({int page = 1, int pageSize = 20}) async {
    final response = await _requestWithRetry(
      () => _dio.get('/api/book-lists/public/browse', queryParameters: {
        'page': page,
        'page_size': pageSize,
      }),
    );
    return response.data as Map<String, dynamic>;
  }

  /// Format a [DioException] into a user-friendly error message.
  // --- Share / Deep Links ---

  Future<Map<String, dynamic>> getShareBook(String googleBookId) async {
    final response = await _dio.get('/api/share/books/$googleBookId');
    return response.data;
  }

  Future<Map<String, dynamic>> getShareList(int listId) async {
    final response = await _dio.get('/api/share/lists/$listId');
    return response.data;
  }

  Future<Map<String, dynamic>> getShareUser(int userId) async {
    final response = await _dio.get('/api/share/users/$userId');
    return response.data;
  }

  // --- Reviews & Ratings ---

  Future<Map<String, dynamic>> getBookReviews(String bookId, {int page = 1, int pageSize = 20, String sort = 'newest'}) async {
    final resp = await _requestWithRetry(() => _dio.get(
      '/api/books/$bookId/reviews',
      queryParameters: {'page': page, 'page_size': pageSize, 'sort': sort},
    ));
    return resp.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createOrUpdateReview(String bookId, {required int rating, String reviewText = ''}) async {
    final resp = await _requestWithRetry(() => _dio.post(
      '/api/books/$bookId/reviews',
      data: {'rating': rating, 'review_text': reviewText},
    ));
    return resp.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateReview(int reviewId, {int? rating, String? reviewText}) async {
    final data = <String, dynamic>{};
    if (rating != null) data['rating'] = rating;
    if (reviewText != null) data['review_text'] = reviewText;
    final resp = await _requestWithRetry(() => _dio.put('/api/reviews/$reviewId', data: data));
    return resp.data as Map<String, dynamic>;
  }

  Future<void> deleteReview(int reviewId) async {
    await _requestWithRetry(() => _dio.delete('/api/reviews/$reviewId'));
  }

  Future<void> voteReviewHelpful(int reviewId) async {
    await _requestWithRetry(() => _dio.post('/api/reviews/$reviewId/helpful'));
  }

  Future<void> removeReviewVote(int reviewId) async {
    await _requestWithRetry(() => _dio.delete('/api/reviews/$reviewId/helpful'));
  }

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

  // ── Compliance / GDPR endpoints ────────────────────────────

  /// Delete the current user's account (GDPR compliance).
  Future<void> deleteMyAccount() async {
    await _requestWithRetry(() => _dio.delete('/api/auth/me'));
  }

  /// Get the current user's privacy consent status.
  Future<Map<String, dynamic>> getPrivacyConsent() async {
    final response = await _requestWithRetry(() => _dio.get('/api/auth/privacy-consent'));
    return response.data as Map<String, dynamic>;
  }

  /// Update the current user's privacy consent preferences.
  Future<void> updatePrivacyConsent({
    required bool analyticsConsent,
    required bool marketingConsent,
  }) async {
    await _requestWithRetry(() => _dio.put('/api/auth/privacy-consent', data: {
      'analytics_consent': analyticsConsent,
      'marketing_consent': marketingConsent,
    }));
  }

  /// Export all user data (GDPR right to data portability).
  Future<Map<String, dynamic>> exportMyData() async {
    final response = await _requestWithRetry(() => _dio.get('/api/auth/export-data'));
    return response.data as Map<String, dynamic>;
  }
}
