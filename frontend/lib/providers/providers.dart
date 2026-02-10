import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/book.dart';
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
    _init();
  }

  Future<void> _init() async {
    final user = await _auth.getStoredUser();
    if (user != null) {
      _api.setAuthToken(user.token);
    }
    state = AsyncValue.data(user);
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final data = await _api.login(email, password);
      final user = User.fromJson(data);
      _api.setAuthToken(user.token);
      await _auth.storeUser(user);
      state = AsyncValue.data(user);
    } on DioException catch (e) {
      final message =
          (e.response?.data as Map<String, dynamic>?)?['detail'] as String? ??
              'Login failed';
      state = AsyncValue.error(message, StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> register(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      final data = await _api.register(email, password);
      final user = User.fromJson(data);
      _api.setAuthToken(user.token);
      await _auth.storeUser(user);
      state = AsyncValue.data(user);
    } on DioException catch (e) {
      final message =
          (e.response?.data as Map<String, dynamic>?)?['detail'] as String? ??
              'Registration failed';
      state = AsyncValue.error(message, StackTrace.current);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
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
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> refresh() async {
    _page = 1;
    state = const AsyncValue.loading();
    final category = ref.read(selectedCategoryProvider);
    try {
      final books = await _fetchBooks(category);
      state = AsyncValue.data(books);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
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
    return api.getLikedBooks();
  }

  Future<void> likeBook(Book book) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.likeBook(book.id);
      final current = state.valueOrNull ?? [];
      if (!current.any((b) => b.id == book.id)) {
        state = AsyncValue.data([book.copyWith(isLiked: true), ...current]);
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> unlikeBook(String bookId) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.unlikeBook(bookId);
      final current = state.valueOrNull ?? [];
      state = AsyncValue.data(current.where((b) => b.id != bookId).toList());
    } catch (e, st) {
      state = AsyncValue.error(e, st);
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
  return api.getBookDetails(bookId);
});
