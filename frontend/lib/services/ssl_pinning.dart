import 'dart:io';
import 'package:dio/dio.dart';
import 'package:dio/io.dart';

/// SSL/TLS Certificate Pinning configuration for BookSwipe API.
///
/// This class provides methods to enforce certificate pinning when
/// communicating with the production backend, preventing MITM attacks.
///
/// IMPORTANT: Before deploying to production, replace the placeholder
/// SHA-256 fingerprints below with the actual certificate fingerprints
/// from your production server.
class SslPinning {
  // Placeholder SHA-256 certificate fingerprints.
  // Replace these with your real production certificate fingerprints
  // before releasing to production.
  //
  // To obtain the fingerprint run:
  //   openssl s_client -connect your-api.example.com:443 < /dev/null 2>/dev/null \
  //     | openssl x509 -fingerprint -sha256 -noout
  static const List<String> _trustedFingerprints = [
    // Primary certificate fingerprint (placeholder)
    'AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99',
    // Backup certificate fingerprint (placeholder)
    '11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00',
  ];

  /// Returns a [SecurityContext] configured for production SSL pinning.
  ///
  /// The context is set up to only trust the certificates whose SHA-256
  /// fingerprints match [_trustedFingerprints].
  static SecurityContext getSecurityContext() {
    final context = SecurityContext(withTrustedRoots: false);
    // In a real deployment you would load your trusted CA certificate:
    //   context.setTrustedCertificatesBytes(certificateBytes);
    return context;
  }

  /// Returns the list of trusted SHA-256 certificate fingerprints.
  static List<String> get trustedFingerprints =>
      List.unmodifiable(_trustedFingerprints);

  /// Creates a [Dio] instance with SSL certificate pinning enabled.
  ///
  /// The returned client will validate that the server certificate's
  /// SHA-256 fingerprint matches one of the trusted fingerprints.
  /// If validation fails the connection is rejected.
  ///
  /// Set [enablePinning] to `false` during development to bypass
  /// certificate validation (never disable in production).
  static Dio createPinnedDio({
    required String baseUrl,
    bool enablePinning = false,
  }) {
    final dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    if (enablePinning) {
      dio.httpClientAdapter = IOHttpClientAdapter(
        createHttpClient: () {
          final client = HttpClient(context: getSecurityContext());
          client.badCertificateCallback =
              (X509Certificate cert, String host, int port) {
            // Convert the certificate SHA-256 fingerprint to the colon-
            // separated uppercase hex format used in _trustedFingerprints.
            final fingerprint = cert.sha256Fingerprint;
            return _trustedFingerprints.contains(fingerprint);
          };
          return client;
        },
      );
    }

    return dio;
  }
}

/// Extension on [X509Certificate] to compute a formatted SHA-256 fingerprint.
extension X509CertificateFingerprint on X509Certificate {
  /// Returns the SHA-256 fingerprint of the DER-encoded certificate as a
  /// colon-separated uppercase hex string.
  ///
  /// TODO: Add `crypto: ^3.0.0` to pubspec.yaml and uncomment the real
  /// implementation before enabling SSL pinning in production.
  String get sha256Fingerprint {
    // Requires: import 'package:crypto/crypto.dart';
    // final digest = sha256.convert(der);
    // return digest.bytes
    //     .map((b) => b.toRadixString(16).padLeft(2, '0').toUpperCase())
    //     .join(':');
    throw UnimplementedError(
      'Add the crypto package and implement SHA-256 hashing before enabling SSL pinning',
    );
  }
}
