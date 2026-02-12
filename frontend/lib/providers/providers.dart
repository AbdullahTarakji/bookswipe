import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
import '../models/category.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

// --- Core Services ---

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());
final authServiceProvider = Provider<AuthService>((ref) => AuthService());

// --- Auth State ---

final authStateProvider =
    StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((ref) {
  return AuthNotifier(ref.read(apiServiceProvider), ref.read(authServiceProvider));
});

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final ApiService _api;
  final AuthService _auth;

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

  Future<void> logout() async {
    _api.clearAuthToken();
    await _auth.clearUser();
    state = const AsyncValue.data(null);
  }
}

// --- Selected Category ---

final selectedCategoryProvider = StateProvider<String?>((ref) => null);

// --- Categories from API ---

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

final discoverBooksProvider =
    AsyncNotifierProvider<DiscoverBooksNotifier, List<Book>>(
        DiscoverBooksNotifier.new);

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

  void removeBook(String bookId) {
    final current = state.valueOrNull ?? [];
    state = AsyncValue.data(current.where((b) => b.id != bookId).toList());
  }
}

// --- Liked Books ---

final likedBooksProvider =
    AsyncNotifierProvider<LikedBooksNotifier, List<Book>>(
        LikedBooksNotifier.new);

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

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }
}

// --- Book Detail ---

final bookDetailProvider =
    FutureProvider.family<Book, String>((ref, bookId) async {
  final api = ref.read(apiServiceProvider);
  try {
    return await api.getBookDetails(bookId);
  } on DioException catch (e) {
    throw ApiService.formatError(e);
  }
});
