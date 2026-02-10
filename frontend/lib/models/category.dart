import 'package:flutter/material.dart';

class BookCategory {
  final String name;
  final String key;
  final IconData icon;
  final Color color;

  const BookCategory({
    required this.name,
    required this.key,
    required this.icon,
    required this.color,
  });

  static const List<BookCategory> defaults = [
    BookCategory(
      name: 'Fiction',
      key: 'fiction',
      icon: Icons.auto_stories,
      color: Color(0xFFFF6B6B),
    ),
    BookCategory(
      name: 'Romance',
      key: 'romance',
      icon: Icons.favorite,
      color: Color(0xFFE91E63),
    ),
    BookCategory(
      name: 'Sci-Fi',
      key: 'science+fiction',
      icon: Icons.rocket_launch,
      color: Color(0xFF9C27B0),
    ),
    BookCategory(
      name: 'Fantasy',
      key: 'fantasy',
      icon: Icons.auto_fix_high,
      color: Color(0xFF673AB7),
    ),
    BookCategory(
      name: 'Thriller',
      key: 'thriller',
      icon: Icons.visibility,
      color: Color(0xFF424242),
    ),
    BookCategory(
      name: 'Mystery',
      key: 'mystery',
      icon: Icons.search,
      color: Color(0xFF795548),
    ),
    BookCategory(
      name: 'Horror',
      key: 'horror',
      icon: Icons.dark_mode,
      color: Color(0xFF212121),
    ),
    BookCategory(
      name: 'Biography',
      key: 'biography',
      icon: Icons.person,
      color: Color(0xFF00897B),
    ),
    BookCategory(
      name: 'History',
      key: 'history',
      icon: Icons.account_balance,
      color: Color(0xFF8D6E63),
    ),
    BookCategory(
      name: 'Science',
      key: 'science',
      icon: Icons.science,
      color: Color(0xFF1976D2),
    ),
    BookCategory(
      name: 'Self-Help',
      key: 'self-help',
      icon: Icons.psychology,
      color: Color(0xFFFF9800),
    ),
    BookCategory(
      name: 'Poetry',
      key: 'poetry',
      icon: Icons.edit_note,
      color: Color(0xFFAD1457),
    ),
    BookCategory(
      name: 'Comics',
      key: 'comics',
      icon: Icons.chat_bubble,
      color: Color(0xFFFDD835),
    ),
    BookCategory(
      name: 'Cooking',
      key: 'cooking',
      icon: Icons.restaurant,
      color: Color(0xFFFF5722),
    ),
  ];
}
