import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'api_service.dart';

/// Handles sharing books, lists, and profiles via the system share sheet.
class ShareService {
  final ApiService _api;

  ShareService(this._api);

  /// Share a book by its Google Book ID.
  Future<void> shareBook(BuildContext context, String googleBookId) async {
    try {
      final data = await _api.getShareBook(googleBookId);
      final url = data['short_url'] ?? data['url'];
      final title = data['og']?['og_title'] ?? 'Check out this book';
      await SharePlus.instance.share(
        ShareParams(text: '$title\n$url'),
      );
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to share')),
        );
      }
    }
  }

  /// Share a book list.
  Future<void> shareList(BuildContext context, int listId) async {
    try {
      final data = await _api.getShareList(listId);
      final url = data['short_url'] ?? data['url'];
      final title = data['og']?['og_title'] ?? 'Check out this reading list';
      await SharePlus.instance.share(
        ShareParams(text: '$title\n$url'),
      );
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to share')),
        );
      }
    }
  }

  /// Share a user profile.
  Future<void> shareUser(BuildContext context, int userId) async {
    try {
      final data = await _api.getShareUser(userId);
      final url = data['short_url'] ?? data['url'];
      final title = data['og']?['og_title'] ?? 'Check out this profile';
      await SharePlus.instance.share(
        ShareParams(text: '$title\n$url'),
      );
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to share')),
        );
      }
    }
  }
}
