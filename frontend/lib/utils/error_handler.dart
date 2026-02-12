import 'package:dio/dio.dart';
import '../services/api_service.dart';

/// Global error handler that converts exceptions into user-friendly messages.
///
/// Maps DioExceptions, API error responses, and generic exceptions to
/// human-readable strings suitable for display in snackbars or error views.
class ErrorHandler {
  /// Convert any exception into a user-friendly message string.
  static String getMessage(Object error) {
    if (error is DioException) {
      return ApiService.formatError(error);
    }
    if (error is String) {
      return error;
    }
    final msg = error.toString();
    // Strip "Exception: " prefix if present
    if (msg.startsWith('Exception: ')) {
      return msg.substring(11);
    }
    return msg;
  }

  /// Whether the error is a network/connectivity issue worth retrying.
  static bool isNetworkError(Object error) {
    if (error is DioException) {
      return error.type == DioExceptionType.connectionError ||
          error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.sendTimeout ||
          error.type == DioExceptionType.receiveTimeout;
    }
    return false;
  }

  /// Whether the error indicates the user needs to re-authenticate.
  static bool isAuthError(Object error) {
    if (error is DioException) {
      return error.response?.statusCode == 401;
    }
    return false;
  }

  /// Whether the error is a server-side issue (5xx).
  static bool isServerError(Object error) {
    if (error is DioException) {
      final code = error.response?.statusCode;
      return code != null && code >= 500;
    }
    return false;
  }
}
