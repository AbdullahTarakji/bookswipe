/// Riverpod providers for subscription state management.
///
/// Wraps RevenueCat on mobile and exposes a unified subscription state
/// that the UI can consume regardless of the billing provider.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../services/revenuecat_service.dart';

// ── Service provider ────────────────────────────────────────

/// Singleton [RevenueCatService] instance.
final revenueCatServiceProvider = Provider<RevenueCatService>((ref) {
  return RevenueCatService();
});

// ── Subscription state ──────────────────────────────────────

/// Immutable snapshot of the user's subscription.
@immutable
class SubscriptionState {
  final bool isPremium;
  final bool isLoading;
  final String? error;
  final Offerings? offerings;

  const SubscriptionState({
    this.isPremium = false,
    this.isLoading = false,
    this.error,
    this.offerings,
  });

  SubscriptionState copyWith({
    bool? isPremium,
    bool? isLoading,
    String? error,
    Offerings? offerings,
  }) {
    return SubscriptionState(
      isPremium: isPremium ?? this.isPremium,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      offerings: offerings ?? this.offerings,
    );
  }
}

// ── Notifier ────────────────────────────────────────────────

/// Manages subscription state and delegates to RevenueCat on mobile.
class SubscriptionNotifier extends StateNotifier<SubscriptionState> {
  final RevenueCatService _rc;

  SubscriptionNotifier(this._rc) : super(const SubscriptionState());

  /// Initialise RevenueCat and load current status + offerings.
  Future<void> init(String userId) async {
    if (!isRevenueCatSupported) return;

    state = state.copyWith(isLoading: true);
    try {
      await _rc.init();
      await _rc.logIn(userId);
      await refresh();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Refresh subscription status and offerings from RevenueCat.
  Future<void> refresh() async {
    if (!isRevenueCatSupported) return;

    state = state.copyWith(isLoading: true);
    try {
      final premium = await _rc.isPremium();
      final offerings = await _rc.getOfferings();
      state = state.copyWith(
        isPremium: premium,
        offerings: offerings,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Purchase a package and update state.
  Future<bool> purchase(Package package) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final info = await _rc.purchasePackage(package);
      if (info == null) {
        // User cancelled
        state = state.copyWith(isLoading: false);
        return false;
      }
      final premium = info.entitlements.all['premium']?.isActive ?? false;
      state = state.copyWith(isPremium: premium, isLoading: false);
      return premium;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      return false;
    }
  }

  /// Restore previous purchases and update state.
  Future<void> restore() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final info = await _rc.restorePurchases();
      final premium = info?.entitlements.all['premium']?.isActive ?? false;
      state = state.copyWith(isPremium: premium, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Log out from RevenueCat (call on app sign-out).
  Future<void> logOut() async {
    await _rc.logOut();
    state = const SubscriptionState();
  }
}

// ── Provider ────────────────────────────────────────────────

final subscriptionProvider =
    StateNotifierProvider<SubscriptionNotifier, SubscriptionState>((ref) {
  final rc = ref.read(revenueCatServiceProvider);
  return SubscriptionNotifier(rc);
});
