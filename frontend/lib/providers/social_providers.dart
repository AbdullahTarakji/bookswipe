import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import 'providers.dart';

// --- Social Profile ---

/// Fetches the current user's social profile.
final socialProfileProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final auth = ref.watch(authStateProvider);
  if (auth.valueOrNull == null) return {};
  final api = ref.read(apiServiceProvider);
  try {
    return await api.getSocialProfile();
  } catch (_) {
    return {};
  }
});

// --- Activity Feed ---

/// Manages the activity feed with pagination.
final activityFeedProvider =
    AsyncNotifierProvider<ActivityFeedNotifier, Map<String, dynamic>>(
        ActivityFeedNotifier.new);

class ActivityFeedNotifier extends AsyncNotifier<Map<String, dynamic>> {
  int _page = 1;

  @override
  Future<Map<String, dynamic>> build() async {
    _page = 1;
    final api = ref.read(apiServiceProvider);
    return api.getActivityFeed(page: _page);
  }

  Future<void> refresh() async {
    _page = 1;
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }

  Future<void> loadPage(int page) async {
    _page = page;
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }
}

// --- Book Lists ---

/// Manages the user's book lists.
final bookListsProvider =
    AsyncNotifierProvider<BookListsNotifier, List<Map<String, dynamic>>>(
        BookListsNotifier.new);

class BookListsNotifier extends AsyncNotifier<List<Map<String, dynamic>>> {
  @override
  Future<List<Map<String, dynamic>>> build() async {
    final auth = ref.watch(authStateProvider);
    if (auth.valueOrNull == null) return [];
    final api = ref.read(apiServiceProvider);
    try {
      final data = await api.getBookLists();
      final lists = data['lists'] as List<dynamic>;
      return lists.map((l) => l as Map<String, dynamic>).toList();
    } on DioException catch (e) {
      throw ApiService.formatError(e);
    }
  }

  Future<void> createList({
    required String name,
    String description = '',
    bool isPublic = true,
  }) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.createBookList(name: name, description: description, isPublic: isPublic);
      ref.invalidateSelf();
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    }
  }

  Future<void> deleteList(int listId) async {
    final api = ref.read(apiServiceProvider);
    try {
      await api.deleteBookList(listId);
      final current = state.valueOrNull ?? [];
      state = AsyncValue.data(current.where((l) => l['id'] != listId).toList());
    } on DioException catch (e) {
      state = AsyncValue.error(ApiService.formatError(e), StackTrace.current);
    }
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    ref.invalidateSelf();
  }
}

// --- User Search ---

/// Tracks the user search query.
final userSearchQueryProvider = StateProvider<String>((ref) => '');

/// Fetches user search results based on the query.
final userSearchProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final query = ref.watch(userSearchQueryProvider);
  if (query.isEmpty) return {'users': [], 'total': 0};
  final api = ref.read(apiServiceProvider);
  try {
    return await api.searchUsers(query);
  } catch (_) {
    return {'users': [], 'total': 0};
  }
});
