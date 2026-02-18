/// RevenueCat service for mobile in-app subscriptions.
///
/// Wraps the `purchases_flutter` SDK to provide a clean interface for
/// initialising RevenueCat, fetching offerings, making purchases,
/// restoring purchases, and checking subscription/entitlement status.
///
/// This service is only used on iOS and Android.  Web clients continue
/// to use Stripe via the API.
library;

import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

/// The entitlement identifier configured in RevenueCat dashboard.
const String _premiumEntitlement = 'premium';

/// RevenueCat API keys per platform — set via compile-time env or config.
const String _iosApiKey = String.fromEnvironment(
  'REVENUECAT_IOS_API_KEY',
  defaultValue: '',
);
const String _androidApiKey = String.fromEnvironment(
  'REVENUECAT_ANDROID_API_KEY',
  defaultValue: '',
);

/// Whether the current platform supports RevenueCat (i.e. not web).
bool get isRevenueCatSupported => !kIsWeb && (Platform.isIOS || Platform.isAndroid);

/// Service layer wrapping RevenueCat SDK operations.
class RevenueCatService {
  bool _initialised = false;

  /// Initialise the RevenueCat SDK.  Should be called once at app startup.
  Future<void> init() async {
    if (!isRevenueCatSupported || _initialised) return;

    final apiKey = Platform.isIOS ? _iosApiKey : _androidApiKey;
    if (apiKey.isEmpty) {
      debugPrint('RevenueCat: API key not configured for ${Platform.operatingSystem}');
      return;
    }

    final config = PurchasesConfiguration(apiKey);
    await Purchases.configure(config);
    _initialised = true;
  }

  /// Identify the user with RevenueCat after authentication.
  ///
  /// This links the RevenueCat subscriber to the backend user ID so that
  /// webhook events contain the correct `app_user_id`.
  Future<void> logIn(String userId) async {
    if (!_initialised) return;
    await Purchases.logIn(userId);
  }

  /// Log out the current RevenueCat user (e.g. on app sign-out).
  Future<void> logOut() async {
    if (!_initialised) return;
    await Purchases.logOut();
  }

  /// Fetch the current offerings from RevenueCat.
  ///
  /// Returns null if RevenueCat is not initialised or no offerings exist.
  Future<Offerings?> getOfferings() async {
    if (!_initialised) return null;
    try {
      return await Purchases.getOfferings();
    } catch (e) {
      debugPrint('RevenueCat getOfferings error: $e');
      return null;
    }
  }

  /// Purchase a package (offering) via the native store.
  ///
  /// Returns the updated [CustomerInfo] on success, or null on cancellation.
  /// Throws on purchase errors other than user cancellation.
  Future<CustomerInfo?> purchasePackage(Package package) async {
    if (!_initialised) return null;
    try {
      final result = await Purchases.purchasePackage(package);
      return result;
    } on PurchasesErrorCode catch (e) {
      if (e == PurchasesErrorCode.purchaseCancelledError) {
        return null; // User cancelled — not an error
      }
      rethrow;
    }
  }

  /// Restore previously purchased subscriptions.
  Future<CustomerInfo?> restorePurchases() async {
    if (!_initialised) return null;
    try {
      return await Purchases.restorePurchases();
    } catch (e) {
      debugPrint('RevenueCat restorePurchases error: $e');
      rethrow;
    }
  }

  /// Check whether the user currently has the premium entitlement.
  Future<bool> isPremium() async {
    if (!_initialised) return false;
    try {
      final info = await Purchases.getCustomerInfo();
      return info.entitlements.all[_premiumEntitlement]?.isActive ?? false;
    } catch (e) {
      debugPrint('RevenueCat isPremium error: $e');
      return false;
    }
  }

  /// Get the current [CustomerInfo] snapshot.
  Future<CustomerInfo?> getCustomerInfo() async {
    if (!_initialised) return null;
    try {
      return await Purchases.getCustomerInfo();
    } catch (e) {
      debugPrint('RevenueCat getCustomerInfo error: $e');
      return null;
    }
  }
}
