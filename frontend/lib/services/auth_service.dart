import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user.dart';

/// Manages secure storage of user credentials using platform-native keystores.
class AuthService {
  static const _userKey = 'bookswipe_user';

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );

  /// Retrieve the previously stored [User] from secure storage, or null.
  Future<User?> getStoredUser() async {
    final json = await _secureStorage.read(key: _userKey);
    if (json == null) return null;
    return User.fromJson(jsonDecode(json) as Map<String, dynamic>);
  }

  /// Persist a [User] (including tokens) to secure storage.
  Future<void> storeUser(User user) async {
    await _secureStorage.write(
      key: _userKey,
      value: jsonEncode(user.toJson()),
    );
  }

  /// Remove all stored user data (used on logout).
  Future<void> clearUser() async {
    await _secureStorage.delete(key: _userKey);
  }
}
