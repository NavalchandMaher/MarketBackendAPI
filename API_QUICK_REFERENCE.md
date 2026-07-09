# Market AI V3 API - Quick Reference Guide for UI Team

## Overview

This is a quick reference guide with curl examples and common implementation patterns for the Market AI V3 API.

---

## Environment Variables

Add these to your development environment:

```
API_BASE_URL=http://localhost:8000
ACCESS_TOKEN=<jwt_access_token>
REFRESH_TOKEN=<jwt_refresh_token>
```

---

## Quick API Test Commands

### 1. User Registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "mobile_number": "+1234567890"
  }'
```

**Expected Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "user_123456",
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

---

### 2. User Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

**Store the tokens securely:**
- Flutter: Use `flutter_secure_storage`
- Web: Use HttpOnly cookies
- React Native: Use `react-native-secure-key-store`

---

### 3. Get Current User Profile

```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

### 4. Get Dashboard

```bash
curl -X GET http://localhost:8000/v3/dashboard \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

### 5. List Strategies

```bash
curl -X GET http://localhost:8000/v3/strategies \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

### 6. Get Market Analysis

```bash
curl -X GET "http://localhost:8000/analysis?symbol=BTCUSDT&timeframe=5m"
```

---

## Common Implementation Patterns

### Pattern 1: Authenticated Request with Error Handling

**Dart/Flutter:**
```dart
Future<Map<String, dynamic>> fetchDashboard(String accessToken) async {
  try {
    final response = await http.get(
      Uri.parse('http://localhost:8000/v3/dashboard'),
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      },
    ).timeout(Duration(seconds: 30));

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      // Token expired - refresh token
      throw Exception('Unauthorized - token expired');
    } else {
      throw Exception('Failed to load dashboard');
    }
  } catch (e) {
    throw Exception('Error: $e');
  }
}
```

---

### Pattern 2: Automatic Token Refresh

```dart
Future<String> getValidAccessToken(String accessToken, String refreshToken) async {
  // Check if token is about to expire
  final decodedToken = JwtDecoder.decode(accessToken);
  final expiryDate = DateTime.fromMillisecondsSinceEpoch(
    decodedToken['exp'] * 1000,
  );

  if (DateTime.now().isAfter(expiryDate.subtract(Duration(minutes: 5)))) {
    // Token expires in less than 5 minutes, refresh it
    final response = await http.post(
      Uri.parse('http://localhost:8000/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // Save new token
      await FlutterSecureStorage().write(
        key: 'access_token',
        value: data['access_token'],
      );
      return data['access_token'];
    }
  }
  
  return accessToken;
}
```

---

### Pattern 3: Loading and Error States

```dart
class ApiState {
  bool isLoading = false;
  String? errorMessage;
  Map<String, dynamic>? data;

  Future<void> fetchData(String endpoint, String token) async {
    isLoading = true;
    errorMessage = null;

    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000$endpoint'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        data = jsonDecode(response.body);
        isLoading = false;
      } else {
        final errorData = jsonDecode(response.body);
        errorMessage = errorData['detail'] ?? 'Unknown error';
        isLoading = false;
      }
    } catch (e) {
      errorMessage = 'Network error: ${e.toString()}';
      isLoading = false;
    }
  }
}
```

---

## API Response Examples

### Dashboard Response

```json
{
  "account_balance": 100000.00,
  "today_pl": 2500.50,
  "open_trades": 3,
  "closed_trades": 47,
  "total_trades": 50,
  "win_rate": 68.5,
  "strategy_name": "Multi-EMA",
  "strategy_version": 2
}
```

### Paper Trading Open Trades Response

```json
[
  {
    "id": "507f1f77bcf86cd799439020",
    "symbol": "BTCUSDT",
    "signal": "BUY",
    "entry_price": 42500.00,
    "current_price": 42750.00,
    "stop_loss": 42200.00,
    "target_price": 43500.00,
    "confidence": 85,
    "pnl": 750.00,
    "pnl_percent": 1.76,
    "status": "OPEN"
  }
]
```

### Strategy List Response

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "strategy_name": "Multi-EMA",
    "version": 2,
    "enabled": true,
    "symbol": "BTCUSDT",
    "timeframe": "5m",
    "created_date": "2026-07-01T10:00:00"
  }
]
```

---

## Error Handling Examples

### 401 Unauthorized

**Response:**
```json
{
  "detail": "Invalid email or password"
}
```

**Action:** 
- Prompt user to login again
- Clear stored tokens
- Redirect to login screen

---

### 422 Validation Error

**Response:**
```json
{
  "detail": "Invalid email format"
}
```

**Action:**
- Show validation error to user
- Highlight invalid field in form

---

### 500 Internal Server Error

**Response:**
```json
{
  "detail": "Internal Server Error"
}
```

**Action:**
- Show generic error message
- Log error for debugging
- Retry after 5 seconds (with max 3 retries)

---

## Performance Optimization Tips

### 1. Implement Caching

```dart
class ApiCache {
  static final Map<String, CachedData> _cache = {};
  
  static Future<T> getCached<T>(
    String key,
    Future<T> Function() fetcher,
    Duration expiry = const Duration(minutes: 5),
  ) async {
    if (_cache.containsKey(key)) {
      final cached = _cache[key]!;
      if (DateTime.now().isBefore(cached.expiryTime)) {
        return cached.data as T;
      }
    }
    
    final data = await fetcher();
    _cache[key] = CachedData(data, DateTime.now().add(expiry));
    return data;
  }
}
```

---

### 2. Pagination for Large Lists

```dart
// Get 50 items, skip first 100
Future<List<dynamic>> getStrategies(int page) async {
  final limit = 50;
  final offset = (page - 1) * limit;
  
  final response = await http.get(
    Uri.parse('http://localhost:8000/v3/strategies?limit=$limit&offset=$offset'),
    headers: {'Authorization': 'Bearer $token'},
  );
  
  return jsonDecode(response.body);
}
```

---

### 3. Batch Requests

```dart
Future<Map<String, dynamic>> fetchDashboardData(String token) async {
  final results = await Future.wait([
    http.get(Uri.parse('http://localhost:8000/v3/dashboard'), 
      headers: {'Authorization': 'Bearer $token'}),
    http.get(Uri.parse('http://localhost:8000/v3/paper/open'), 
      headers: {'Authorization': 'Bearer $token'}),
    http.get(Uri.parse('http://localhost:8000/v3/strategies'), 
      headers: {'Authorization': 'Bearer $token'}),
  ]);
  
  return {
    'dashboard': jsonDecode(results[0].body),
    'openTrades': jsonDecode(results[1].body),
    'strategies': jsonDecode(results[2].body),
  };
}
```

---

## Common Endpoints for UI Implementation

### Authentication Screens
1. **Register:** `POST /auth/register`
2. **Login:** `POST /auth/login`
3. **Forgot Password:** `POST /auth/forgot-password`
4. **Change Password:** `POST /auth/change-password`

### Dashboard Screen
1. **Get Dashboard:** `GET /v3/dashboard`
2. **Get Open Trades:** `GET /v3/paper/open`
3. **Get Account:** `GET /v3/account`

### Analysis Screen
1. **Get Analysis:** `GET /analysis?symbol=BTCUSDT&timeframe=5m`
2. **Get Symbols:** `GET /v3/symbols`
3. **Get Timeframes:** `GET /v3/timeframes`

### Trades Screen
1. **Get Open Trades:** `GET /v3/paper/open`
2. **Get Trade History:** `GET /v3/paper/history`
3. **Get Statistics:** `GET /v3/paper/statistics`

### Reports Screen
1. **Get Dashboard Report:** `GET /v3/reports/dashboard`
2. **Get Daily Report:** `GET /v3/reports/daily`
3. **Get Equity Curve:** `GET /v3/reports/equity`

### Settings Screen
1. **Get Settings:** `GET /v3/settings`
2. **Update Settings:** `PUT /v3/settings`
3. **Get Account:** `GET /v3/account`
4. **Update Account:** `PUT /v3/account`

### Strategy Management
1. **List Strategies:** `GET /v3/strategies`
2. **Get Strategy:** `GET /v3/strategies/{id}`
3. **Create Strategy:** `POST /v3/strategies`
4. **Update Strategy:** `PUT /v3/strategies/{id}`
5. **Delete Strategy:** `DELETE /v3/strategies/{id}`

---

## Testing Checklist

- [ ] Register new user
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should show error)
- [ ] Get user profile
- [ ] Update user profile
- [ ] Logout user
- [ ] Refresh token
- [ ] Forgot password
- [ ] Get dashboard data
- [ ] Get open trades
- [ ] Get trade history
- [ ] Get strategies
- [ ] Create new strategy
- [ ] Update strategy
- [ ] Delete strategy
- [ ] Run backtest
- [ ] Get reports

---

## Debugging Tips

### 1. Log All Requests and Responses

```dart
void logRequest(String method, String url, Map<String, String> headers, String? body) {
  print('→ $method $url');
  print('Headers: $headers');
  if (body != null) print('Body: $body');
}

void logResponse(int statusCode, String body) {
  print('← Status: $statusCode');
  print('Response: $body');
}
```

---

### 2. Use Network Monitor

- Chrome DevTools Network tab
- Postman for API testing
- Charles Proxy for request inspection

---

### 3. Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Token expired | Refresh token |
| 422 Validation Error | Invalid data | Check request body format |
| Network timeout | Slow connection | Increase timeout, add retry |
| CORS error | Missing headers | Add Content-Type header |
| Empty response | API error | Check status code and error detail |

---

## Support

For API integration support:
- Check `API_DOCUMENTATION.md` for complete details
- Review `api_endpoints.json` for endpoint structure
- Test endpoints using provided curl commands
- Contact backend team for API issues

---

**Last Updated:** July 2026  
**Version:** 3.0.0
