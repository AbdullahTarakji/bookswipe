import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
import '../models/category.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

// --- Core Services ---

/// Provides the singleton [ApiService] instance for HTTP communication.
final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

/// Provides the singleton [AuthService] instance for secure token storage.
final authServiceProvider = Provider<AuthService>((ref) => AuthService());

// --- Auth State ---

/// Manages the current authentication state (loading, authenticated, or unauthenticated).
final authStateProvider =
    StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  return AuthNotifier(ref.read(apiServiceProvider), ref.read(authServiceProvider));
});

/// Notifier that handles login, registration, OAuth, and session restoration.
class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final ApiService _api;
  final AuthService _auth;

  /// Creates an [AuthNotifier] and immediately begins restoring any saved session.
  AuthNotifier(this._api, this._auth) : super(const AsyncValue.loading()) {
    _setupTokenRefresh();
    _init();
  }

  void _setupTokenRefresh() {
    _api.onTokenRefreshNeeded = (accessToken, refreshToken) async {
      final currentUser = state.valueOrNull;
      if (currentUser != null) {
        final updatedUser = currentUser.copyWithTokens(
          token: accessToken,
          refreshToken: refreshToken,
        );
        await _auth.storeUser(updatedUser);
        state = AsyncValue.data(updatedUser);
      }
    };
  }

  Future<void> _init() async {
    try {
      final user = await _auth.getStoredUser();
      if (user != null && user.token.isNotEmpty) {
        _api.setAuthToken(user.token);
        if (user.refreshToken.isNotEmpty) {
          _api.setRefreshToken(user.refreshToken);
        }
        // Try to fetch profile to validate token and get up-to-date info
        try {
          final profile = await _api.getProfile();
          final updatedUser = User(
            id: (profile['id'] ?? user.id).toString(),
            email: profile['email'] as String? ?? user.email,
            token: user.token,
            refreshToken: user.refreshToken,
            role: profile['role'] as String? ?? user.role,
            subscriptionStatus: profile['subscription_status'] as String? ?? user.subscriptionStatus,
            subscriptionPlan: profile['subscription_plan'] as String? ?? user.subscriptionPlan,
            subscriptionEndDate: profile['subscription_end_date'] as String?,
          );
          await _auth.storeUser(updatedUser);
          state = AsyncValue.data(updatedUser);
        } on DioException {
          // Token may be expired but interceptor will handle refresh
          state = AsyncValue.data(user);
        }
      } else {
        state = const AsyncValue.data(null);
      }
    } catch (e) {
      state = const AsyncValue.data(null);
    }
  }

  /// Authenticate with email and password. Sets error state on failure.
  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final tokenData = await _api.login(email, password);
      final accessToken = tokenData['access_token'] as String;
      final refreshToken = tokenData['refresh_token'] as String? ?? '';

      _api.setAuthToken(accessToken);
      _api.setRefreshToken(refreshToken);

      // Fetch user profile
      Map<String, dynamic>? profile;
      try {
        profile = await _api.getProfile();
      } catch (_) {}

      final user = User(
        id: (profile?['id'] ?? '').toString(),
        email: profile?['email'] as String? ?? email,
        token: accessToken,
        refreshToken: refreshToken,
        role: profile?['role'] as String? ?? 'user',
        subscriptionStatus: profile?['subscription_status'] as String? ?? 'free',
        subscriptionPlan: profile?['subscription_plan'] as String? ?? 'free',
        subscriptionEndDate: profile?['subscription_end_date'] as String?,
      );

      await _auth.storeUser(user);
      state = AsyncValue.data(user);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Login failed. Please try again.', st);
    }
  }

  /// Register a new account. Sets error state on failure.
  Future<void> register(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final tokenData = await _api.register(email, password);
      final accessToken = tokenData['access_token'] as String;
      final refreshToken = tokenData['refresh_token'] as String? ?? '';

      _api.setAuthToken(accessToken);
      _api.setRefreshToken(refreshToken);

      // Fetch user profile
      Map<String, dynamic>? profile;
      try {
        profile = await _api.getProfile();
      } catch (_) {}

      final user = User(
        id: (profile?['id'] ?? '').toString(),
        email: profile?['email'] as String? ?? email,
        token: accessToken,
        refreshToken: refreshToken,
        role: profile?['role'] as String? ?? 'user',
        subscriptionStatus: profile?['subscription_status'] as String? ?? 'free',
        subscriptionPlan: profile?['subscription_plan'] as String? ?? 'free',
        subscriptionEndDate: profile?['subscription_end_date'] as String?,
      );

      await _auth.storeUser(user);
      state = AsyncValue.data(user);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Registration failed. Please try again.', st);
    }
  }

  /// Sign in with a Google OAuth ID token. Sets error state on failure.
  Future<void> signInWithGoogle(String idToken) async {
    state = const AsyncValue.loading();
    try {
      final tokenData = await _api.googleSignIn(idToken);
      await _handleOAuthTokenResponse(tokenData);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Google sign-in failed. Please try again.', st);
    }
  }

  /// Sign in with Apple OAuth credentials. Sets error state on failure.
  Future<void> signInWithApple({
    required String authorizationCode,
    required String identityToken,
  }) async {
    state = const AsyncValue.loading();
    try {
      final tokenData = await _api.appleSignIn(
        authorizationCode: authorizationCode,
        identityToken: identityToken,
      );
      await _handleOAuthTokenResponse(tokenData);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Apple sign-in failed. Please try again.', st);
    }
  }

  Future<void> _handleOAuthTokenResponse(Map<String, dynamic> tokenData) async {
    final accessToken = tokenData['access_token'] as String;
    final refreshToken = tokenData['refresh_token'] as String? ?? '';

    _api.setAuthToken(accessToken);
    _api.setRefreshToken(refreshToken);

    Map<String, dynamic>? profile;
    try {
      profile = await _api.getProfile();
    } catch (_) {}

    final user = User(
      id: (profile?['id'] ?? '').toString(),
      email: profile?['email'] as String? ?? '',
      token: accessToken,
      refreshToken: refreshToken,
      role: profile?['role'] as String? ?? 'user',
      subscriptionStatus: profile?['subscription_status'] as String? ?? 'free',
      subscriptionPlan: profile?['subscription_plan'] as String? ?? 'free',
      subscriptionEndDate: profile?['subscription_end_date'] as String?,
    );

    await _auth.storeUser(user);
    state = AsyncValue.data(user);
  }

  /// Refresh subscription status from the server.
  Future<void> refreshSubscription() async {
    final currentUser = state.valueOrNull;
    if (currentUser == null) return;
    try {
      final profile = await _api.getProfile();
      final updatedUser = currentUser.copyWithSubscription(
        subscriptionStatus: profile['subscription_status'] as String? ?? 'free',
        subscriptionPlan: profile['subscription_plan'] as String? ?? 'free',
        subscriptionEndDate: profile['subscription_end_date'] as String?,
      );
      await _auth.storeUser(updatedUser);
      state = AsyncValue.data(updatedUser);
    } catch (_) {}
  }

  /// Clear all authentication state and stored tokens.
  Future<void> logout() async {
    _api.clearAuthToken();
    await _auth.clearUser();
    state = const AsyncValue.data(null);
  }
}

// --- Selected Category ---

/// Tracks the currently selected category for book discovery filtering.
final selectedCategoryProvider = StateProvider<String?>((ref) => null);

// --- Categories from API ---

/// Fetches book categories from the API, falling back to local defaults on failure.
final categoriesProvider = FutureProvider<List<BookCategory>>((ref) async {
  final api = ref.read(apiServiceProvider);
  try {
    final data = await api.getCategories();
    return data.map((c) {
      final key = c['google_category_key'] as String? ?? c['name'] as String;
      final name = c['name'] as String;
      // Match with local icon/color mapping, fall back to defaults
      final localMatch = BookCategory.defaults.where(
        (d) => d.key == key || d.name.toLowerCase() == name.toLowerCase(),
      );
      if (localMatch.isNotEmpty) {
        return BookCategory(
          name: name,
          key: key,
          icon: localMatch.first.icon,
          color: localMatch.first.color,
        );
      }
      return BookCategory(
        name: name,
        key: key,
        icon: Icons.book,
        color: const Color(0xFF607D8B),
      );
    }).toList();
  } catch (_) {
    // Fall back to hardcoded defaults if API fails
    return BookCategory.defaults;
  }
});

// --- Books Discovery ---

/// Provides the list of books available for discovery (swipe).
final discoverBooksProvider =
    AsyncNotifierProvider<DiscoverBooksNotifier, List<Book>>(
        DiscoverBooksNotifier.new);

/// Notifier that manages book discovery state including pagination and error recovery.
class DiscoverBooksNotifier extends AsyncNotifier<List<Book>> {
  int _page = 1;
  bool _isLoadingMore = false;
  bool _hasMore = true;

  /// Last swiped book for undo/rewind.
  Book? _lastSwiped;
  bool _lastSwipedWasLike = false;

  /// Number of remaining cards that triggers a prefetch of the next page.
  static const int _prefetchThreshold = 5;

  @override
  Future<List<Book>> build() async {
    _page = 1;
    _isLoadingMore = false;
    _hasMore = true;
    _lastSwiped = null;
    final category = ref.watch(selectedCategoryProvider);
    return _fetchBooks(category);
  }

  Future<List<Book>> _fetchBooks(String? category) async {
    final api = ref.read(apiServiceProvider);
    return api.discoverBooks(category: category, page: _page);
  }

  /// Load the next page of books and append to the current list.
  /// Guarded against concurrent calls — safe to call repeatedly.
  Future<void> loadMore() async {
    if (_isLoadingMore || !_hasMore) return;
    _isLoadingMore = true;
    final category = ref.read(selectedCategoryProvider);
    _page++;
    try {
      final moreBooks = await _fetchBooks(category);
      if (moreBooks.isEmpty) {
        _hasMore = false;
      }
      final current = state.valueOrNull ?? [];
      state = AsyncValue.data([...current, ...moreBooks]);
    } on DioException catch (e) {
      // Don't overwrite current data on loadMore failure, revert page
      _page--;
      final current = state.valueOrNull;
      if (current != null) {
        state = AsyncValue.data(current);
      } else {
        state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
      }
    } catch (e, st) {
      _page--;
      state = AsyncValue.error('Failed to load more books', st);
    } finally {
      _isLoadingMore = false;
    }
  }

  /// Call from the swiper's onSwipe to prefetch when running low on cards.
  void maybeLoadMore(int remainingCards) {
    if (remainingCards <= _prefetchThreshold) {
      loadMore();
    }
  }

  /// Reset pagination and reload books from scratch.
  Future<void> refresh() async {
    _page = 1;
    _isLoadingMore = false;
    _hasMore = true;
    state = const AsyncValue.loading();
    final category = ref.read(selectedCategoryProvider);
    try {
      final books = await _fetchBooks(category);
      state = AsyncValue.data(books);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Failed to load books', st);
    }
  }

  /// Track the last swiped book so it can be undone.
  void setLastSwiped(Book book, {required bool wasLiked}) {
    _lastSwiped = book;
    _lastSwipedWasLike = wasLiked;
  }

  /// Undo the last swipe — re-inserts the book at the front of the stack.
  /// If it was a like, also unlikes it via the API.
  void undoLastSwipe() {
    final book = _lastSwiped;
    if (book == null) return;
    _lastSwiped = null;

    // Re-insert at front
    final current = state.valueOrNull ?? [];
    state = AsyncValue.data([book, ...current]);

    // If it was a like, undo the like
    if (_lastSwipedWasLike) {
      ref.read(likedBooksProvider.notifier).unlikeBook(book.id);
    }
  }

  /// Remove a book from the discovery list (e.g. after swiping).
  void removeBook(String bookId) {
    final current = state.valueOrNull ?? [];
    state = AsyncValue.data(current.where((b) => b.id != bookId).toList());
  }
}

// --- Liked Books ---

/// Provides the list of books the current user has liked.
final likedBooksProvider =
    AsyncNotifierProvider<LikedBooksNotifier, List<Book>>(
        LikedBooksNotifier.new);

/// Notifier that manages the liked books list with optimistic updates.
class LikedBooksNotifier extends AsyncNotifier<List<Book>> {
  @override
  Future<List<Book>> build() async {
    final auth = ref.watch(authStateProvider);
    if (auth.valueOrNull == null) return [];
    final api = ref.read(apiServiceProvider);
    try {
      return await api.getLikedBooks();
    } on DioException catch (e) {
      throw ApiService.formatError(e);
    }
  }

  /// Add a book to the liked list with optimistic UI update.
  Future<void> likeBook(Book book) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.likeBook(book);
      final current = state.valueOrNull ?? [];
      if (!current.any((b) => b.id == book.id)) {
        state = AsyncValue.data([book.copyWith(isLiked: true), ...current]);
      }
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Failed to like book', st);
    }
  }

  /// Remove a book from the liked list.
  Future<void> unlikeBook(String bookId) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.unlikeBook(bookId);
      final current = state.valueOrNull ?? [];
      state = AsyncValue.data(current.where((b) => b.id != bookId).toList());
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Failed to unlike book', st);
    }
  }

  /// Reload the liked books list from the server.
  Future<void> refresh() async {
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }
}

// --- Book Detail ---

/// Fetches detailed information for a single book by its ID.
final bookDetailProvider =
    FutureProvider.family<Book, String>((ref, bookId) async {
  final api = ref.read(apiServiceProvider);
  try {
    return await api.getBookDetails(bookId);
  } on DioException catch (e) {
    throw ApiService.formatError(e);
  }
});

// --- Swipe Status ---

/// Fetches the current user's swipe status (count, limit, premium).
final swipeStatusProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final auth = ref.watch(authStateProvider);
  if (auth.valueOrNull == null) {
    return {'swipes_today': 0, 'daily_limit': 10, 'is_premium': false, 'swipes_remaining': 10};
  }
  final api = ref.read(apiServiceProvider);
  try {
    return await api.getSwipeStatus();
  } catch (_) {
    return {'swipes_today': 0, 'daily_limit': 10, 'is_premium': false, 'swipes_remaining': 10};
  }
});

// --- Admin ---

/// Fetches admin analytics data.
final adminAnalyticsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiServiceProvider);
  return api.getAnalytics();
});

/// Fetches system info for admin panel.
final adminSystemInfoProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(apiServiceProvider);
  return api.getSystemInfo();
});

/// Manages the admin user list with pagination, search, and filtering.
final adminUsersProvider =
    AsyncNotifierProvider<AdminUsersNotifier, Map<String, dynamic>>(
        AdminUsersNotifier.new);

class AdminUsersNotifier extends AsyncNotifier<Map<String, dynamic>> {
  int _page = 1;
  String? _search;
  String? _roleFilter;
  bool? _bannedFilter;

  @override
  Future<Map<String, dynamic>> build() async {
    final api = ref.read(apiServiceProvider);
    return api.getAdminUsers(
      page: _page,
      search: _search,
      role: _roleFilter,
      isBanned: _bannedFilter,
    );
  }

  Future<void> setFilters({String? search, String? role, bool? isBanned}) async {
    _page = 1;
    _search = search;
    _roleFilter = role;
    _bannedFilter = isBanned;
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }

  Future<void> setPage(int page) async {
    _page = page;
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }
}
