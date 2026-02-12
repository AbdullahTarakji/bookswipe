/// Represents an authenticated user with their JWT tokens.
class User {
  final String id;
  final String email;
  final String token;
  final String refreshToken;
  final String role;

  const User({
    required this.id,
    required this.email,
    required this.token,
    this.refreshToken = '',
    this.role = 'user',
  });

  bool get isAdmin => role == 'admin';

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['id'] ?? '').toString(),
      email: json['email'] as String? ?? '',
      token: json['token'] as String? ?? json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
      role: json['role'] as String? ?? 'user',
    );
  }

  User copyWithTokens({required String token, required String refreshToken}) {
    return User(
      id: id,
      email: email,
      token: token,
      refreshToken: refreshToken,
      role: role,
    );
  }

  User copyWith({
    String? id,
    String? email,
    String? token,
    String? refreshToken,
    String? role,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      token: token ?? this.token,
      refreshToken: refreshToken ?? this.refreshToken,
      role: role ?? this.role,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'token': token,
        'refresh_token': refreshToken,
        'role': role,
      };
}
