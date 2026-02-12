/// Riverpod providers for BookSwipe state management.
///
/// All API calls flow through providers — screens never call services directly.
/// Providers are the single source of truth for application state.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
import '../models/category.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

// --- Core Services ---

/// Provides the singleton [ApiService] for HTTP communication.
final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

/// Provides the singleton [AuthService] for secure token storage.
final authServiceProvider = Provider<AuthService>((ref) => AuthService());

// --- Auth State ---

/// Manages authentication state including login, registration, and logout.
final authStateProvider =
    StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  return AuthNotifier(ref.read(apiServiceProvider), ref.read(authServiceProvider));
});

/// Notifier that manages user authentication state and token lifecycle.
class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final ApiService _api;
  final AuthService _auth;

  /// Creates an [AuthNotifier] and initializes auth state from secure storage.
  AuthNotifier(this._api, this._auth) : super(const AsyncValue.loading()) {
    _setupTokenRefresh();
    _init();
  }

  void _setupTokenRefresh() {
    _api.onTokenRefreshNeeded = (refreshToken) async {
      final currentUser = state.valueOrNull;
      if (currentUser != null) {
        final updatedUser = currentUser.copyWithTokens(
          token: _api.toString(), // Will be set by interceptor
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

  /// Authenticate with email and password, storing tokens on success.
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
      );

      await _auth.storeUser(user);
      state = AsyncValue.data(user);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Login failed. Please try again.', st);
    }
  }

  /// Register a new account with email and password, storing tokens on success.
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
      );

      await _auth.storeUser(user);
      state = AsyncValue.data(user);
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error('Registration failed. Please try again.', st);
    }
  }

  /// Authenticate with Google OAuth, exchanging an ID token for app tokens.
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

  /// Authenticate with Apple Sign In, exchanging identity token for app tokens.
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
    );

    await _auth.storeUser(user);
    state = AsyncValue.data(user);
  }

  /// Clear authentication tokens and sign the user out.
  Future<void> logout() async {
    _api.clearAuthToken();
    await _auth.clearUser();
    state = const AsyncValue.data(null);
  }
}

// --- Selected Category ---

/// Tracks the currently selected category filter key, or null for all.
final selectedCategoryProvider = StateProvider<String?>((ref) => null);

// --- Categories from API ---

/// Fetches categories from the API, falling back to hardcoded defaults.
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

/// Manages the list of books available for swiping/discovery.
final discoverBooksProvider =
    AsyncNotifierProvider<DiscoverBooksNotifier, List<Book>>(
        DiscoverBooksNotifier.new);

/// Notifier for book discovery with pagination, skipping, and refresh support.
class DiscoverBooksNotifier extends AsyncNotifier<List<Book>> {
  int _page = 1;

  @override
  Future<List<Book>> build() async {
    _page = 1;
    final category = ref.watch(selectedCategoryProvider);
    return _fetchBooks(category);
  }

  Future<List<Book>> _fetchBooks(String? category) async {
    final api = ref.read(apiServiceProvider);
    return api.discoverBooks(category: category, page: _page);
  }

  /// Load the next page of books and append to the current list.
  Future<void> loadMore() async {
    final category = ref.read(selectedCategoryProvider);
    _page++;
    try {
      final moreBooks = await _fetchBooks(category);
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
    }
  }

  /// Reset pagination and reload books from the first page.
  Future<void> refresh() async {
    _page = 1;
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

  /// Skip a book via the API and remove it from the local list.
  Future<void> skipBook(String bookId) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.skipBook(bookId);
    } catch (_) {
      // Skip failures are non-critical; the book is already removed from view
    }
  }

  /// Remove a book from the local list without an API call.
  void removeBook(String bookId) {
    final current = state.valueOrNull ?? [];
    state = AsyncValue.data(current.where((b) => b.id != bookId).toList());
  }
}

// --- Liked Books ---

/// Manages the user's liked books list with like/unlike/refresh support.
final likedBooksProvider =
    AsyncNotifierProvider<LikedBooksNotifier, List<Book>>(
        LikedBooksNotifier.new);

/// Notifier for the user's liked books, synced with the backend.
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

  /// Like a book and add it to the local list optimistically.
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

  /// Unlike a book and remove it from the local list.
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

  /// Refresh the liked books list from the server.
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
