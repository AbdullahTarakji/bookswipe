/// Represents an authenticated user with their access and refresh tokens.
class User {
  final String id;
  final String email;
  final String token;
  final String refreshToken;

  const User({
    required this.id,
    required this.email,
    required this.token,
    this.refreshToken = '',
  });

  /// Creates a [User] from a JSON map (supports both API and storage formats).
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['id'] ?? '').toString(),
      email: json['email'] as String? ?? '',
      token: json['token'] as String? ?? json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
    );
  }

  /// Creates a copy of this user with updated authentication tokens.
  User copyWithTokens({required String token, required String refreshToken}) {
    return User(
      id: id,
      email: email,
      token: token,
      refreshToken: refreshToken,
    );
  }

  /// Serializes this user to a JSON map for secure storage.
  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'token': token,
        'refresh_token': refreshToken,
      };
}
