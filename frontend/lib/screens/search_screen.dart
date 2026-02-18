import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/providers.dart';
import '../widgets/empty_state.dart';

/// Unified search screen with filter chips, recent searches, and tabbed results.
class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen>
    with SingleTickerProviderStateMixin {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  Timer? _debounce;

  late TabController _tabController;

  String _searchType = 'all';
  String? _categoryFilter;
  String? _authorFilter;

  Map<String, dynamic>? _results;
  List<Map<String, dynamic>> _history = [];
  List<String> _suggestions = [];
  bool _loading = false;
  bool _showSuggestions = false;

  static const _categories = [
    'Fiction',
    'Romance',
    'Mystery',
    'Sci-Fi',
    'Fantasy',
    'Thriller',
    'Biography',
    'History',
    'Self-Help',
    'Science',
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadHistory();
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    _debounce?.cancel();
    _tabController.dispose();
    super.dispose();
  }

  void _onTabChanged() {
    if (!_tabController.indexIsChanging) {
      final types = ['all', 'books', 'users', 'lists'];
      setState(() => _searchType = types[_tabController.index]);
      if (_controller.text.trim().isNotEmpty) _performSearch();
    }
  }

  Future<void> _loadHistory() async {
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.getSearchHistory(limit: 10);
      if (mounted) {
        setState(() {
          _history = (data['items'] as List<dynamic>)
              .map((e) => e as Map<String, dynamic>)
              .toList();
        });
      }
    } catch (_) {}
  }

  void _onQueryChanged(String query) {
    _debounce?.cancel();
    if (query.trim().isEmpty) {
      setState(() {
        _suggestions = [];
        _showSuggestions = false;
      });
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      try {
        final api = ref.read(apiServiceProvider);
        final suggestions = await api.getAutocompleteSuggestions(query.trim());
        if (mounted && _controller.text.trim() == query.trim()) {
          setState(() {
            _suggestions = suggestions;
            _showSuggestions = suggestions.isNotEmpty;
          });
        }
      } catch (_) {}
    });
  }

  Future<void> _performSearch() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _loading = true;
      _showSuggestions = false;
    });

    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.unifiedSearch(
        query,
        searchType: _searchType,
        category: _categoryFilter,
        author: _authorFilter,
      );
      if (mounted) {
        setState(() {
          _results = data;
          _loading = false;
        });
        _loadHistory();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Search failed: $e')),
        );
      }
    }
  }

  Future<void> _clearHistory() async {
    try {
      final api = ref.read(apiServiceProvider);
      await api.clearSearchHistory();
      if (mounted) setState(() => _history = []);
    } catch (_) {}
  }

  void _selectSuggestion(String suggestion) {
    _controller.text = suggestion;
    _controller.selection = TextSelection.fromPosition(
      TextPosition(offset: suggestion.length),
    );
    _performSearch();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Search'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'All'),
            Tab(text: 'Books'),
            Tab(text: 'Users'),
            Tab(text: 'Lists'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  decoration: InputDecoration(
                    hintText: 'Search books, users, lists...',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _controller.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _controller.clear();
                              setState(() {
                                _results = null;
                                _suggestions = [];
                                _showSuggestions = false;
                              });
                            },
                          )
                        : null,
                  ),
                  textInputAction: TextInputAction.search,
                  onChanged: _onQueryChanged,
                  onSubmitted: (_) => _performSearch(),
                ),
                // Filter chips
                if (_searchType == 'all' || _searchType == 'books')
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: SizedBox(
                      height: 36,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: [
                          for (final cat in _categories)
                            Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: FilterChip(
                                label: Text(cat),
                                selected: _categoryFilter == cat.toLowerCase(),
                                onSelected: (selected) {
                                  setState(() {
                                    _categoryFilter =
                                        selected ? cat.toLowerCase() : null;
                                  });
                                  if (_controller.text.trim().isNotEmpty) {
                                    _performSearch();
                                  }
                                },
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // Suggestions dropdown
          if (_showSuggestions)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.1),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: _suggestions
                    .map((s) => ListTile(
                          dense: true,
                          leading: const Icon(Icons.search, size: 18),
                          title: Text(s),
                          onTap: () => _selectSuggestion(s),
                        ))
                    .toList(),
              ),
            ),

          // Content
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _results != null
                    ? _buildResults(theme)
                    : _buildRecentSearches(theme),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentSearches(ThemeData theme) {
    if (_history.isEmpty) {
      return const EmptyState(
        icon: Icons.search,
        title: 'Start searching',
        subtitle: 'Find books, people, and reading lists',
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Recent Searches',
                  style: theme.textTheme.titleSmall),
              TextButton(
                onPressed: _clearHistory,
                child: const Text('Clear All'),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _history.length,
            itemBuilder: (context, index) {
              final item = _history[index];
              return ListTile(
                leading: const Icon(Icons.history, size: 20),
                title: Text(item['query'] as String? ?? ''),
                dense: true,
                onTap: () {
                  _controller.text = item['query'] as String? ?? '';
                  _performSearch();
                },
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildResults(ThemeData theme) {
    final books =
        (_results?['books'] as List<dynamic>?) ?? [];
    final users =
        (_results?['users'] as List<dynamic>?) ?? [];
    final lists =
        (_results?['lists'] as List<dynamic>?) ?? [];

    final hasResults = books.isNotEmpty || users.isNotEmpty || lists.isNotEmpty;

    if (!hasResults) {
      return const EmptyState(
        icon: Icons.search_off,
        title: 'No results found',
        subtitle: 'Try a different search term or adjust filters',
      );
    }

    return ListView(
      children: [
        if (books.isNotEmpty) ...[
          _sectionHeader(theme, 'Books', _results?['total_books'] ?? 0),
          ...books.map((b) => _buildBookTile(b as Map<String, dynamic>, theme)),
        ],
        if (users.isNotEmpty) ...[
          _sectionHeader(theme, 'Users', _results?['total_users'] ?? 0),
          ...users.map((u) => _buildUserTile(u as Map<String, dynamic>, theme)),
        ],
        if (lists.isNotEmpty) ...[
          _sectionHeader(theme, 'Lists', _results?['total_lists'] ?? 0),
          ...lists.map((l) => _buildListTile(l as Map<String, dynamic>, theme)),
        ],
      ],
    );
  }

  Widget _sectionHeader(ThemeData theme, String title, int total) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Text(
        '$title ($total)',
        style: theme.textTheme.titleSmall?.copyWith(
          color: theme.colorScheme.primary,
        ),
      ),
    );
  }

  Widget _buildBookTile(Map<String, dynamic> book, ThemeData theme) {
    final title = book['title'] as String? ?? '';
    final authors = (book['authors'] as List<dynamic>?)?.join(', ') ?? '';
    final bookId = book['google_book_id'] as String? ?? '';

    return ListTile(
      leading: const Icon(Icons.menu_book),
      title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(authors, maxLines: 1, overflow: TextOverflow.ellipsis),
      onTap: bookId.isNotEmpty ? () => context.push('/book/$bookId') : null,
    );
  }

  Widget _buildUserTile(Map<String, dynamic> user, ThemeData theme) {
    final username = user['username'] as String? ?? '';
    final userId = user['user_id'] as int? ?? 0;

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.primaryContainer,
        child: Icon(Icons.person,
            color: theme.colorScheme.onPrimaryContainer, size: 20),
      ),
      title: Text(username),
      subtitle: Text(user['bio'] as String? ?? ''),
      onTap: () => context.push('/social/profile/$userId'),
    );
  }

  Widget _buildListTile(Map<String, dynamic> list, ThemeData theme) {
    final name = list['name'] as String? ?? '';
    final listId = list['id'] as int? ?? 0;
    final owner = list['username'] as String? ?? '';
    final count = list['item_count'] as int? ?? 0;

    return ListTile(
      leading: const Icon(Icons.list),
      title: Text(name, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text('by $owner · $count books'),
      onTap: () => context.push('/social/lists/$listId'),
    );
  }
}
